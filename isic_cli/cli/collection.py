import click
from rich.console import Console
from rich.table import Table

from isic_cli.cli.context import IsicContext
from isic_cli.cli.utils import suggest_guest_login
from isic_cli.io.http import get_collections


@click.group(short_help='Manage collections.')
@click.pass_obj
def collection(ctx: IsicContext):
    pass


@collection.command(name='list')
@click.pass_obj
@suggest_guest_login
def list_(ctx: IsicContext):
    table = Table('ID', 'Name', 'Public')

    collections = sorted(get_collections(ctx.session), key=lambda coll: coll['name'])
    for collection in collections:
        table.add_row(str(collection['id']), collection['name'], str(collection['public']))

    console = Console()
    console.print(table)
