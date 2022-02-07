from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
import os
import platform
import sys
import traceback

from girder_cli_oauth_client import GirderCliOAuthClient
from packaging.version import parse as parse_version
import requests
from requests.exceptions import RequestException
import typer

from isic_cli.image import image
from isic_cli.metadata import metadata

try:
    __version__ = version('isic-cli')
except PackageNotFoundError:
    # package is not installed
    pass


def get_oauth_client():
    client = GirderCliOAuthClient('https://api.isic-archive.com/oauth', '')
    return client


def login(ctx: typer.Context):
    ctx.obj.login()
    print('hello')


def make_app():
    app = typer.Typer()
    app.add_typer(image, name='image')
    app.add_typer(metadata, name='metadata')
    app.command('login')(login)

    @app.callback()
    def main(ctx: typer.Context):
        ctx.obj = get_oauth_client()
        ctx.obj.maybe_restore_login()

    return app


def newer_version_available():
    if __version__ is None:
        return False

    this_version = parse_version(__version__)
    if this_version.is_devrelease:
        return False

    r = requests.get('https://pypi.org/pypi/isic-cli/json', timeout=(5, 5))
    r.raise_for_status()
    releases = [parse_version(v) for v in r.json()['releases'].keys()]
    for release in releases:
        if not (release.is_prerelease or release.is_devrelease) and release > this_version:
            return True
    return False


def check_for_newer_version():
    try:
        if newer_version_available():
            typer.echo(
                typer.style(
                    """There is a newer version of isic-cli available.
You must upgrade to the latest version before continuing.
If you are using pip, then you can upgrade by running the following command:
""",
                    fg='yellow',
                ),
                err=True,
            )
            typer.echo(typer.style('pip install --upgrade isic-cli', fg='green'), err=True)
            sys.exit(1)
    except RequestException:
        typer.echo(
            typer.style('Failed to check for newer version of isic-cli:', fg='red'), err=True
        )
        raise


def cli():
    app = make_app()

    if not os.environ.get('OFFLINE'):
        check_for_newer_version()

    try:
        app()
    except Exception:
        typer.echo(
            typer.style(
                'The following unexpected error occurred while attempting your operation:\n',
                fg=typer.colors.RED,
            ),
            err=True,
        )

        typer.echo(traceback.format_exc(), err=True)

        # TODO: maybe use scooby?
        typer.echo(f'isic-cli: v{__version__}', err=True)
        typer.echo(f'python:   v{platform.python_version()}', err=True)
        typer.echo(f'time:     {datetime.utcnow().isoformat()}', err=True)
        typer.echo(f'os:       {platform.platform()}', err=True)
        # TODO: try to scrape auth credentials?
        typer.echo(f'command:  isic {" ".join(sys.argv[1:])}\n', err=True)

        typer.echo(
            typer.style(
                'This is a bug in isic-cli and should be reported. You can open an issue below: ',
                fg=typer.colors.YELLOW,
            ),
            err=True,
        )
        typer.echo(
            'https://github.com/ImageMarkup/isic-cli/issues/new',
            err=True,
        )
