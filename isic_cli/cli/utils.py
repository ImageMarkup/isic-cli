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
