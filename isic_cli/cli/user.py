from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from authlib.integrations.base_client.errors import OAuthError
import click

if TYPE_CHECKING:
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
        try:
            obj.oauth.login()
        except OAuthError as e:
            if e.error == "invalid_grant":
                click.secho(
                    "Logging in timed out or had an unexpected error. Please try again.", fg="red"
                )
                sys.exit(1)
            else:
                raise
        else:
            click.secho("Success!", fg="green")


@user.command()
@click.pass_obj
def logout(obj: IsicContext):
    """Logout of the ISIC Archive."""
    obj.oauth.logout()


@user.command(hidden=True)
@click.pass_obj
def print_token(obj: IsicContext):
    obj.oauth._load()  # noqa: SLF001
    click.echo(json.dumps(obj.oauth._session.token, indent=4))  # noqa: SLF001
