import json

import click

from isic_cli.cli.context import IsicContext


@click.group(short_help="Manage authentication with the ISIC Archive.")
@click.pass_obj
def user(ctx):
    pass


@user.command()
@click.pass_obj
def login(obj: IsicContext):
    """Login to the ISIC Archive."""
    if obj.user:
        click.echo(f'Hello {obj.user["email"]}!')
    else:
        obj.oauth.login()
        click.echo("Success!")


@user.command()
@click.pass_obj
def logout(obj: IsicContext):
    """Logout of the ISIC Archive."""
    obj.oauth.logout()


@user.command(hidden=True)
@click.pass_obj
def print_token(obj: IsicContext):
    obj.oauth._load()
    click.echo(json.dumps(obj.oauth._session.token, indent=4))
