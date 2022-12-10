import logging
import re
import sys
from typing import Optional

import click
from humanize.number import intcomma
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from isic_cli.cli.context import IsicContext
from isic_cli.cli.types import CollectionId
from isic_cli.cli.utils import require_login, suggest_guest_login
from isic_cli.io.http import bulk_collection_operation, get_collections

logger = logging.getLogger(__name__)


def _parse_isic_ids(ctx, param, value) -> list[str]:
    isic_ids = {line.strip() for line in value.read().splitlines() if line.strip() != ""}
    for isic_id in isic_ids:
        if not re.match(r"^ISIC_\d{7}$", isic_id):
            click.secho(f'Found invalidly formatted ISIC ID: "{isic_id}"', err=True, fg="red")
            sys.exit(1)

    return list(isic_ids)


def _table_from_summary(summary: dict[str, list[str]], nice_map: Optional[dict] = None):
    nice_map = {} if nice_map is None else nice_map
    table = Table()

    table.add_column("Status")
    table.add_column("Num instances", justify="right")
    table.add_column("Examples", justify="right")

    def examples(isic_ids: list) -> str:
        s = set(isic_ids)
        ret = ", ".join(sorted(list(s)[:3]))
        if len(s) > 3:
            ret += ", etc."
        else:
            ret += "."
        return ret

    table.add_row(
        nice_map["succeeded"], str(len(summary["succeeded"])), examples(summary["succeeded"])
    )

    for k, v in summary.items():
        if k != "succeeded":  # already printed
            table.add_row(nice_map[k], str(len(v)), examples(v))

    return table


@click.group(short_help="Manage collections.")
@click.pass_obj
def collection(ctx: IsicContext):
    pass


@collection.command(name="list", help="List collections.")
@click.pass_obj
@suggest_guest_login
def list_(ctx: IsicContext):
    table = Table("ID", "Name", "Public", "Pinned", "Locked", "DOI")

    collections = sorted(get_collections(ctx.session), key=lambda coll: coll["name"])
    for collection in collections:
        table.add_row(
            str(collection["id"]),
            collection["name"],
            str(collection["public"]),
            str(collection["pinned"]),
            str(collection["locked"]),
            str(collection["doi"]),
        )

    console = Console()
    console.print(table)


@collection.command(name="add-images", help="Add images to a collection.")
@click.argument("collection_id", type=CollectionId(locked_okay=False))
@click.option(
    "--from-isic-ids",
    type=click.File("r"),
    callback=_parse_isic_ids,
    required=True,
    help=(
        "Provide a path to a line delimited list of ISIC IDs to add to a collection. "
        "Alternatively, - allows stdin to be used."
    ),
)
@click.pass_obj
@require_login
def add_images(ctx: IsicContext, collection_id: int, from_isic_ids: list[str]):
    # TODO: fix this import
    from isic_cli.cli import DOMAINS

    with Progress(console=Console(file=sys.stderr)) as progress:
        task = progress.add_task(
            f"Adding images ({intcomma(len(from_isic_ids))} total)", total=len(from_isic_ids)
        )
        summary = bulk_collection_operation(
            ctx.session, collection_id, "populate-from-list", from_isic_ids, progress, task
        )

    table = _table_from_summary(
        summary,
        nice_map={
            "succeeded": "[green]Image added[/]",
            "no_perms_or_does_not_exist": "[red]Image not found or inaccessible[/]",
            "private_image_public_collection": "[red]Image is private, collection is public[/]",
        },
    )

    Console().print(table)

    if summary["succeeded"]:
        click.echo()
        click.echo(f"View your collection: {DOMAINS[ctx.env]}/collections/{collection_id}/")


@collection.command(name="remove-images", help="Remove images from a collection.")
@click.argument("collection_id", type=CollectionId(locked_okay=False))
@click.option(
    "--from-isic-ids",
    type=click.File("r"),
    callback=_parse_isic_ids,
    required=True,
    help=(
        "Provide a path to a line delimited list of ISIC IDs to remove from a collection. "
        "Alternatively, - allows stdin to be used."
    ),
)
@click.pass_obj
@require_login
def remove_images(ctx: IsicContext, collection_id: int, from_isic_ids: list[str]):
    # TODO: fix this import
    from isic_cli.cli import DOMAINS

    with Progress(console=Console(file=sys.stderr)) as progress:
        task = progress.add_task(
            f"Removing images ({intcomma(len(from_isic_ids))} total)", total=len(from_isic_ids)
        )
        summary = bulk_collection_operation(
            ctx.session, collection_id, "remove-from-list", from_isic_ids, progress, task
        )

    table = _table_from_summary(
        summary,
        nice_map={
            "succeeded": "[green]Image removed[/]",
            "no_perms_or_does_not_exist": "[red]Image not found or inaccessible[/]",
        },
    )

    Console().print(table)

    if summary["succeeded"]:
        click.echo()
        click.echo(f"View your collection: {DOMAINS[ctx.env]}/collections/{collection_id}/")
