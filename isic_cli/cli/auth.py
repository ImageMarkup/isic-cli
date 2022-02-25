import json

import click

from isic_cli.cli.context import IsicContext


@click.group(short_help='Manage authentication with the ISIC Archive.')
@click.pass_obj
def auth(ctx):
    pass


@auth.command()
@click.pass_obj
def login(obj: IsicContext):
    """Login to the ISIC Archive."""
    if obj.logged_in:
        r = obj.session.get('users/me')
        r.raise_for_status()
        click.echo(f'Hello {r.json()["email"]}!')
    else:
        obj.oauth.login()
        click.echo('Success!')


@auth.command()
@click.pass_obj
def logout(obj: IsicContext):
    """Logout of the ISIC Archive."""
    obj.oauth.logout()


@auth.command(hidden=True)
@click.pass_obj
def print_token(obj: IsicContext):
    obj.oauth._load()
    click.echo(json.dumps(obj.oauth._session.token, indent=4))
