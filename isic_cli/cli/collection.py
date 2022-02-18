import logging
import re
import sys

import click
from rich.console import Console
from rich.table import Table

from isic_cli.cli.context import IsicContext
from isic_cli.cli.types import CollectionId
from isic_cli.cli.utils import require_login, suggest_guest_login
from isic_cli.io.http import get_collections

logger = logging.getLogger(__name__)


@click.group(short_help='Manage collections.')
@click.pass_obj
def collection(ctx: IsicContext):
    pass


@collection.command(name='list', help='List collections.')
@click.pass_obj
@suggest_guest_login
def list_(ctx: IsicContext):
    table = Table('ID', 'Name', 'Public', 'Official', 'DOI')

    collections = sorted(get_collections(ctx.session), key=lambda coll: coll['name'])
    for collection in collections:
        table.add_row(
            str(collection['id']),
            collection['name'],
            str(collection['public']),
            str(collection['official']),
            str(collection['doi']),
        )

    console = Console()
    console.print(table)


@collection.command(name='add-images', help='Add images to a collection.')
@click.argument('collection_id', type=CollectionId())
@click.option(
    '--from-isic-ids',
    type=click.File('r'),
    required=True,
    help=(
        'Provide a path to a line delimited list of ISIC IDs to add to a collection. '
        'Alternatively, - allows stdin to be used.'
    ),
)
@click.pass_obj
@require_login
def add_images(ctx: IsicContext, collection_id: int, from_isic_ids):
    # TODO: fix this import
    from isic_cli.cli import DOMAINS

    # TODO: maybe move this to a type
    isic_ids = set(
        (line.strip() for line in from_isic_ids.read().splitlines() if line.strip() != '')
    )
    for isic_id in isic_ids:
        if not re.match(r'^ISIC_\d{7}$', isic_id):
            click.secho(f'Found invalidly formatted ISIC ID: "{isic_id}"', err=True, fg='red')
            sys.exit(1)

    r = ctx.session.post(f'collections/{collection_id}/populate-from-list/', {'isic_ids': isic_ids})
    if 400 <= r.status_code <= 500:
        click.secho(f'Failed to add images, error: \n{r.text}', fg='red', err=True)
        sys.exit(1)
    r.raise_for_status()

    click.echo(
        f'Adding {len(isic_ids)} images to collection {collection_id}. It may take several minutes.'
    )
    click.echo(f'View the results at: {DOMAINS[ctx.env]}/collections/{collection_id}/')
