from collections import defaultdict
import csv
import io
import itertools
from pathlib import Path
import sys

import click
from click.types import IntRange
from humanize import intcomma
from isic_metadata.metadata import MetadataBatch, MetadataRow, convert_errors
from isic_metadata.utils import get_unstructured_columns
from pydantic import ValidationError
from rich.console import Console
from rich.progress import Progress, track
from rich.table import Table

from isic_cli.cli.context import IsicContext
from isic_cli.cli.types import CommaSeparatedIdentifiers, SearchString
from isic_cli.cli.utils import _extract_metadata, suggest_guest_login
from isic_cli.io.http import get_images, get_num_images


@click.group(short_help="Manage metadata.")
@click.pass_obj
def metadata(obj):
    pass


@metadata.command(name="validate")
@click.argument(
    "csv_file",
    type=click.File("r"),
)
def validate(csv_file: io.BufferedReader):
    """Validate metadata from a local csv."""
    console = Console()

    # get number of rows in csv
    num_rows = sum(1 for _ in csv_file)
    csv_file.seek(0)

    reader = csv.DictReader(csv_file)
    headers = reader.fieldnames

    if not headers:
        click.secho("No rows found in csv!", fg="red")
        sys.exit(1)

    # batch problems apply to the overall csv and can't be computed without looking at the
    # entire csv.
    batch_problems: list[dict] = []

    # keyed by column, message
    column_problems: dict[tuple[str, str], list[int]] = defaultdict(list)

    batch_items: list[MetadataRow] = []

    # start enumerate at 2 to account for header row and 1-indexing
    for i, row in track(
        enumerate(reader, start=2), total=num_rows, description="Validating metadata"
    ):
        if row.get("patient_id") or row.get("lesion_id"):
            batch_items.append(
                MetadataRow(patient_id=row.get("patient_id"), lesion_id=row.get("lesion_id"))
            )
        try:
            MetadataRow.model_validate(row)
        except ValidationError as e:
            for error in convert_errors(e):
                column = error["loc"][0] if error["loc"] else ""
                column_problems[(column, error["msg"])].append(i)

    try:
        MetadataBatch(
            items=batch_items,
        )
    except ValidationError as e:
        for error in e.errors():
            batch_problems.append(error)

    if batch_problems:
        table = Table(title="Batch Level Errors Found")

        table.add_column("Error", style="magenta")
        table.add_column("Num instances", justify="right", style="green")
        table.add_column("Examples")

        for error in batch_problems:
            table.add_row(
                error["msg"],
                str(len(error["ctx"]["examples"])),
                ", ".join(error["ctx"]["examples"][0:3]),
            )

        console.print(table)

    if column_problems:
        table = Table(title="Row Level Errors Found")

        table.add_column("Field", justify="right", style="cyan", no_wrap=True)
        table.add_column("Error", style="magenta")
        table.add_column("Num instances", justify="right", style="green")
        table.add_column("Rows", justify="right", style="green")

        last_row_field = None
        for k, v in dict(sorted(column_problems.items())).items():
            field = k[0] if last_row_field != k[0] else ""
            last_row_field = k[0]
            rows_affected = ", ".join(map(str, v[:5]))
            end = ", etc" if len(v) > 5 else ""
            table.add_row(field, k[1], str(len(v)), f"{rows_affected}{end}")

        console.print(table)

    if batch_problems or column_problems:
        sys.exit(1)
    else:
        click.secho("No structural errors found!", fg="green")

    unstructured_columns = get_unstructured_columns(headers)
    if unstructured_columns:
        table = Table(title="Unrecognized Fields")
        table.add_column("Field", justify="left", style="cyan", no_wrap=True)

        for field in unstructured_columns:
            table.add_row(field)

        console.print(table)


@metadata.command(name="download")
@click.option(
    "-s",
    "--search",
    type=SearchString(),
    default="",
    help='e.g. "diagnosis:melanoma AND age_approx:50"',
)
@click.option(
    "-c",
    "--collections",
    type=CommaSeparatedIdentifiers(),
    default="",
    help=(
        "Filter the images based on a comma separated list of collection ids e.g. 2,17,42. "
        "See isic collection list to obtain ids."
    ),
)
@click.option(
    "-l",
    "--limit",
    default=0,
    metavar="INTEGER",
    type=IntRange(min=0),
    help="Download at most LIMIT metadata records. Use a value of 0 to download all records.",
)
@click.option(
    "-o",
    "--outfile",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    help="A filepath to write the output CSV to.",
)
@click.pass_obj
@suggest_guest_login
def download(
    ctx: IsicContext,
    search: str,
    collections: str,
    limit: int,
    outfile: Path,
):
    """
    Download metadata from the ISIC Archive.

    The search query uses a simple DSL syntax.

    Some example queries are:

    age_approx:50 AND diagnosis:melanoma

    age_approx:[20 TO 40] AND sex:male

    anatom_site_general:*torso AND image_type:dermoscopic
    """
    archive_num_images = get_num_images(ctx.session, search, collections)
    download_num_images = archive_num_images if limit == 0 else min(archive_num_images, limit)
    nice_num_images = intcomma(download_num_images)
    images = itertools.islice(get_images(ctx.session, search, collections), download_num_images)

    with Progress(console=Console(file=sys.stderr)) as progress:
        task = progress.add_task(
            f"Downloading metadata records ({nice_num_images})", total=download_num_images
        )
        headers, records = _extract_metadata(images, progress, task)

    if records:
        if outfile:
            stream = click.open_file(outfile, "w", encoding="utf8")
        else:
            stream = click.get_text_stream("stdout", encoding="utf8")

        writer = csv.DictWriter(stream, headers)
        writer.writeheader()
        for record in records:
            writer.writerow(record)
