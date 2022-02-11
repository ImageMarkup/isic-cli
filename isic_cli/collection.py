from rich.console import Console
from rich.table import Table
import typer

from isic_cli.session import get_session
from isic_cli.utils import get_collections

collection = typer.Typer()


@collection.command(name='list')
def list_(
    ctx: typer.Context,
):
    with get_session(ctx.obj.auth_headers) as session:
        table = Table('ID', 'Name', 'Public')

        collections = sorted(get_collections(session), key=lambda coll: coll['name'])
        for collection in collections:
            table.add_row(str(collection['id']), collection['name'], str(collection['public']))

        console = Console()
        console.print(table)
