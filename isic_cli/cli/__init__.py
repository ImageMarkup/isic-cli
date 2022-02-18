from datetime import datetime
from http.client import HTTPConnection
import logging
import platform
import sys
import traceback

import click
from click import UsageError

from isic_cli.cli.collection import collection as collection_group
from isic_cli.cli.context import IsicContext
from isic_cli.cli.image import image as image_group
from isic_cli.cli.login import login, logout
from isic_cli.cli.metadata import metadata as metadata_group
from isic_cli.oauth import get_oauth_client
from isic_cli.session import get_session
from isic_cli.utils.version import check_for_newer_version, get_version

DOMAINS = {
    'dev': 'http://127.0.0.1:8000',
    'sandbox': 'https://api-sandbox.isic-archive.com',
    'prod': 'https://api.isic-archive.com',
}


@click.group()
@click.option(
    '--guest', is_flag=True, default=False, help='Simulate a non logged in user.', hidden=True
)
@click.option(
    '--sandbox',
    is_flag=True,
    default=False,
    help='Execute against the ISIC Archive sandbox.',
    hidden=True,
    envvar='ISIC_SANDBOX',
)
@click.option(
    '--dev',
    is_flag=True,
    default=False,
    help='Execute against a dev ISIC Archive environment.',
    hidden=True,
    envvar='ISIC_DEV',
)
@click.option(
    '--no-version-check',
    is_flag=True,
    default=False,
    help='Disable the version upgrade check.',
    hidden=True,
)
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose mode.')
@click.version_option()
@click.pass_context
def cli(ctx, verbose: bool, guest: bool, sandbox: bool, dev: bool, no_version_check: bool):
    if verbose:
        requests_log = logging.getLogger('requests.packages.urllib3')
        HTTPConnection.debuglevel = 1

        for logger in (logging.getLogger('isic_cli'), requests_log):
            logger.addHandler(logging.StreamHandler(sys.stderr))
            logger.setLevel(logging.DEBUG)

    if sandbox and dev:
        raise UsageError('Illegal usage: --sandbox is mutually exclusive with --dev.')

    env = 'prod'
    if sandbox:
        env = 'sandbox'
    elif dev:
        env = 'dev'

    if not no_version_check:
        check_for_newer_version()

    oauth = get_oauth_client(f'{DOMAINS[env]}/oauth')

    if not guest:
        oauth.maybe_restore_login()
    with get_session(f'{DOMAINS[env]}/api/v2/', oauth.auth_headers) as session:
        ctx.obj = IsicContext(
            oauth=oauth,
            session=session,
            logged_in=bool(oauth.auth_headers),
            env=env,
            verbose=verbose,
        )


cli.add_command(collection_group, name='collection')
cli.add_command(image_group, name='image')
cli.add_command(metadata_group, name='metadata')
cli.add_command(login, name='login')
cli.add_command(logout, name='logout')


def main():
    try:
        cli()
    except Exception:
        click.echo(
            click.style(
                'The following unexpected error occurred while attempting your operation:\n',
                fg='red',
            ),
            err=True,
        )

        click.echo(traceback.format_exc(), err=True)

        # TODO: maybe use scooby?
        click.echo(f'isic-cli: v{get_version()}', err=True)
        click.echo(f'python:   v{platform.python_version()}', err=True)
        click.echo(f'time:     {datetime.utcnow().isoformat()}', err=True)
        click.echo(f'os:       {platform.platform()}', err=True)
        # TODO: try to scrape auth credentials?
        click.echo(f'command:  isic {" ".join(sys.argv[1:])}\n', err=True)

        click.echo(
            click.style(
                'This is a bug in isic-cli and should be reported. You can open an issue below: ',
                fg='yellow',
            ),
            err=True,
        )
        click.echo(
            'https://github.com/ImageMarkup/isic-cli/issues/new',
            err=True,
        )
