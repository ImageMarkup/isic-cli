from collections import defaultdict
import csv
import itertools
from pathlib import Path
import sys
from typing import OrderedDict, Union

import click
from click.types import IntRange
from humanize import intcomma
from isic_metadata.metadata import MetadataRow
from isic_metadata.utils import get_unstructured_columns
import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress, track
from rich.table import Table

from isic_cli.cli.context import IsicContext
from isic_cli.cli.types import CommaSeparatedIdentifiers, SearchString
from isic_cli.cli.utils import suggest_guest_login
from isic_cli.io.http import get_images, get_num_images


@click.group(short_help='Manage metadata.')
@click.pass_obj
def metadata(obj):
    pass


@metadata.command(name='validate')
@click.argument(
    'csv_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True)
)
def validate(csv_path: Path):
    """Validate metadata from a local csv."""
    console = Console()
    with open(csv_path) as csv:
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

        sys.exit(1)

    unstructured_columns = get_unstructured_columns(df)
    if unstructured_columns:
        table = Table(title='Unrecognized Fields')
        table.add_column('Field', justify='left', style='cyan', no_wrap=True)

        for field in unstructured_columns:
            table.add_row(field)

        console.print(table)


@metadata.command(name='download')
@click.option('-s', '--search', type=SearchString(), help='e.g. "diagnosis:melanoma AND age:50"')
@click.option(
    '-c',
    '--collections',
    type=CommaSeparatedIdentifiers(),
    help=(
        'Limit the images based on a comma separated list of collection ids e.g. 2,17,42. '
        'See isic collection list to obtain ids.'
    ),
)
@click.option(
    '-l',
    '--limit',
    default=1_000,
    metavar='INTEGER',
    type=IntRange(min=0),
    help='Use a value of 0 to disable the limit.',
)
@click.pass_obj
@suggest_guest_login
def download(ctx: IsicContext, search: Union[None, str], collections: Union[None, str], limit: int):
    """
    Download metadata from the ISIC Archive.

    The search query uses a simple DSL syntax.

    Some example queries are:

    age_approx:50 AND diagnosis:melanoma

    age_approx:[20 TO 40] AND sex:male

    anatom_site_general:*torso AND image_type:dermoscopic
    """
    num_results = get_num_images(ctx.session, search, collections)
    if limit > 0:
        num_results = min(num_results, limit)

    images = get_images(ctx.session, search, collections)

    if limit > 0:
        images = itertools.islice(images, limit)

    with Progress(console=Console(file=sys.stderr)) as progress:
        task = progress.add_task(
            f'Downloading metadata records ({intcomma( num_results )} total)', total=num_results
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
