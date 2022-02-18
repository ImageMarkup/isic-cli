import sys

import click

from isic_cli.cli.context import IsicContext


def suggest_guest_login(f):
    def decorator(ctx: IsicContext, **kwargs):
        if not ctx.logged_in:
            click.echo(
                "Psst, you're logged out. Logging in with `isic login` might return more data.\n",
                err=True,
            )
        f(ctx, **kwargs)

    return decorator


def require_login(f):
    def decorator(ctx: IsicContext, **kwargs):
        if not ctx.logged_in:
            click.echo(
                'This command requires a logged in user, use the `isic login` command to continue.',
                err=True,
            )
            sys.exit(1)

        f(ctx, **kwargs)

    return decorator
