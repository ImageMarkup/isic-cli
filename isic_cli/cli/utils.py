import sys

import click

from isic_cli.cli.context import IsicContext


def suggest_guest_login(f):
    def decorator(ctx: IsicContext, **kwargs):
        if not ctx.logged_in:
            click.echo(
                "Psst, you're logged out. Logging in with `isic auth login` might return more data.\n",  # noqa: E501
                err=True,
            )
        f(ctx, **kwargs)

    return decorator


def require_login(f):
    def decorator(ctx: IsicContext, **kwargs):
        if not ctx.logged_in:
            click.echo(
                'This command requires a logged in user, use the `isic auth login` command to continue.',  # noqa: E501
                err=True,
            )
            sys.exit(1)

        f(ctx, **kwargs)

    return decorator
