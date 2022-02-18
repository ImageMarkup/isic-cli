import click

from isic_cli.cli.context import IsicContext
from isic_cli.cli.utils import require_login


@click.command()
@click.pass_obj
def login(obj: IsicContext):
    """Login through the ISIC Archive."""
    if obj.logged_in:
        r = obj.session.get('users/me')
        r.raise_for_status()
        click.echo(f'Hello {r.json()["email"]}!')
    else:
        obj.oauth.login()


@click.command()
@click.pass_obj
@require_login
def logout(obj: IsicContext):
    """Logout of the ISIC Archive."""
    obj.oauth.logout()
