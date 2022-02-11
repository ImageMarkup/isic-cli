from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
import logging
import os
import platform
import sys
import traceback

from girder_cli_oauth_client import GirderCliOAuthClient
from pkg_resources import parse_version
import requests
from requests.exceptions import RequestException
import typer

from isic_cli.collection import collection
from isic_cli.image import image
from isic_cli.metadata import metadata
from isic_cli.session import get_session


def get_version():
    try:
        return version('isic-cli')
    except PackageNotFoundError:
        # package is not installed
        return None


def get_oauth_client():
    client = GirderCliOAuthClient(
        os.environ.get('ISIC_OAUTH_URL', 'https://api.isic-archive.com/oauth'),
        os.environ.get('ISIC_OAUTH_CLIENT_ID', 'RpCzc4hFjv5gOJdM2DM2nBdokOviOh5ne63Tpn7Q'),
    )
    return client


def login(ctx: typer.Context):
    """Login through the ISIC Archive."""
    if ctx.obj.auth_headers:
        with get_session(ctx.obj.auth_headers) as session:
            r = session.get('users/me')
            r.raise_for_status()
            typer.echo(f'Hello {r.json()["email"]}')
    else:
        ctx.obj.login()


def make_app():
    app = typer.Typer()
    app.add_typer(collection, name='collection', help='Manage collections.')
    app.add_typer(image, name='image', help='Manage images.')
    app.add_typer(metadata, name='metadata', help='Manage metadata.')
    app.command('login')(login)

    @app.callback()
    def main(ctx: typer.Context, verbose: bool = False):
        if verbose:
            from http.client import HTTPConnection

            requests_log = logging.getLogger('requests.packages.urllib3')
            HTTPConnection.debuglevel = 1
            requests_log.addHandler(logging.StreamHandler(sys.stderr))
            requests_log.setLevel(logging.DEBUG)

        ctx.obj = get_oauth_client()
        ctx.obj.maybe_restore_login()
        if not ctx.obj.auth_headers:
            typer.echo(
                "Psst, you're logged out. Logging in with `isic login` might return more data.\n",
                err=True,
            )

    return app


def newer_version_available():
    if get_version() is None:
        return False

    this_version = parse_version(get_version())
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
        typer.echo(f'isic-cli: v{get_version()}', err=True)
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
