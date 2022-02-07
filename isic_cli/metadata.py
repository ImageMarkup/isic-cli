from collections import defaultdict
from pathlib import Path
from typing import OrderedDict

from isic_metadata.metadata import MetadataRow
from isic_metadata.utils import get_unstructured_columns
import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import track
from rich.table import Table
import typer

metadata = typer.Typer()


@metadata.command(name='validate')
def validate_metadata(csv_file: Path):
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
