from collections import defaultdict
import csv
import itertools
from pathlib import Path
import sys
from typing import OrderedDict

from isic_metadata.metadata import MetadataRow
from isic_metadata.utils import get_unstructured_columns
import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress, track
from rich.table import Table
import typer

from isic_cli.session import get_session
from isic_cli.utils import get_images, get_num_images

metadata = typer.Typer()


@metadata.command(name='validate')
def validate_metadata(csv_file: Path):
    """Validate metadata from a local csv."""
    console = Console()
    with open(csv_file) as csv:
        df = pd.read_csv(csv, header=0)

    # pydantic expects None for the absence of a value, not NaN
    df = df.replace({np.nan: None})

    # keyed by column, message
    column_problems: dict[tuple[str, str], list[int]] = defaultdict(list)

    for i, (_, row) in track(enumerate(df.iterrows(), start=2), total=len(df)):
        try:
            MetadataRow.parse_obj(row)
        except Exception as e:
            for error in e.errors():
                column = error['loc'][0]
                column_problems[(column, error['msg'])].append(i)

    errors = OrderedDict(sorted(column_problems.items()))

    if errors:
        table = Table(title='Errors found')

        table.add_column('Field', justify='right', style='cyan', no_wrap=True)
        table.add_column('Error', style='magenta')
        table.add_column('Num instances', justify='right', style='green')
        table.add_column('Rows', justify='right', style='green')

        last_row_field = None
        for k, v in errors.items():
            field = k[0] if last_row_field != k[0] else ''
            last_row_field = k[0]
            rows_affected = ', '.join(map(str, v[:5]))
            end = ', etc' if len(v) > 5 else ''
            table.add_row(field, k[1], str(len(v)), f'{rows_affected}{end}')

        console.print(table)

    unstructured_columns = get_unstructured_columns(df)
    if unstructured_columns:
        table = Table(title='Unrecognized Fields')
        table.add_column('Field', justify='left', style='cyan', no_wrap=True)

        for field in unstructured_columns:
            table.add_row(field)

        console.print(table)


@metadata.command(name='download')
def download(
    ctx: typer.Context,
    search: str = typer.Option(''),
    collections: str = typer.Option(
        '',
        help='Limit the images based on a comma separated string of collection ids (see isic collection list).',  # noqa: E501
    ),
    max_results: int = typer.Option(1_000, min=0, help='Use a value of 0 to disable the limit.'),
):
    """
    Download metadata from the ISIC Archive.

    The search query uses a simple DSL syntax.

    Some example queries are:

    age_approx:50 AND diagnosis:melanoma

    age_approx:[20 TO 40] AND sex:male

    anatom_site_general:*torso AND image_type:dermoscopic
    """
    with get_session(ctx.obj.auth_headers) as session:
        num_results = get_num_images(session, search, collections)
        if max_results > 0:
            num_results = min(num_results, max_results)

        images = get_images(session, search, collections)

        if max_results > 0:
            images = itertools.islice(images, max_results)

        with Progress(console=Console(file=sys.stderr)) as progress:
            task = progress.add_task(
                f'Fetching metadata records ({num_results})', total=num_results
            )

            fieldnames = set()
            records = []
            for image in images:
                fieldnames |= set(image.get('metadata', {}).keys())
                records.append({**{'isic_id': image['isic_id']}, **image['metadata']})
                progress.update(task, advance=1)

        if records:
            writer = csv.DictWriter(sys.stdout, ['isic_id'] + list(sorted(fieldnames)))
            writer.writeheader()
            for record in records:
                writer.writerow(record)
