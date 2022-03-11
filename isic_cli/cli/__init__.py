from datetime import datetime
from http.client import HTTPConnection
import logging
import platform
import sys
import traceback

from authlib.integrations.base_client.errors import OAuthError
import click
from click import UsageError, get_current_context
from requests.exceptions import HTTPError

from isic_cli.cli.accession import accession as accession_group
from isic_cli.cli.collection import collection as collection_group
from isic_cli.cli.context import IsicContext
from isic_cli.cli.image import image as image_group
from isic_cli.cli.metadata import metadata as metadata_group
from isic_cli.cli.user import user as user_group
from isic_cli.io.http import get_users_me
from isic_cli.oauth import get_oauth_client
from isic_cli.session import get_session
from isic_cli.utils.version import check_for_newer_version, get_version

DOMAINS = {
    'dev': 'http://127.0.0.1:8000',
    'sandbox': 'https://api-sandbox.isic-archive.com',
    'prod': 'https://api.isic-archive.com',
}

logger = logging.getLogger(__name__)


@click.group(context_settings={'help_option_names': ['-h', '--help']}, no_args_is_help=True)
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
    logger.addHandler(logging.StreamHandler(sys.stderr))
    logger.setLevel(logging.WARN)

    if verbose:
        HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger('requests.packages.urllib3')
        requests_log.addHandler(logging.StreamHandler(sys.stderr))
        requests_log.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    if sandbox and dev:
        raise UsageError('Illegal usage: --sandbox is mutually exclusive with --dev.')

    env = 'prod'
    if sandbox:
        env = 'sandbox'
    elif dev:
        env = 'dev'

    if no_version_check:
        logger.warning('Disabling the version check could cause errors.')
    else:
        check_for_newer_version()

    oauth = get_oauth_client(f'{DOMAINS[env]}/oauth')

    if not guest:
        try:
            oauth.maybe_restore_login()
        except OAuthError as e:
            # This is really rare, but in the event of a refresh token being revoked
            # (this happens in dev all the time) the restoration will fail with an
            # invalid_grant error.
            logger.debug(e)
            oauth.logout()
            click.secho(
                'Something went wrong with restoring a login, you may need to log back in.',
                fg='yellow',
            )

    with get_session(f'{DOMAINS[env]}/api/v2/', oauth.auth_headers) as session:
        user = None
        if oauth.auth_headers:
            try:
                user = get_users_me(session)
            except HTTPError as e:
                if e.response.status_code == 404:
                    # perhaps a stale token
                    oauth.logout()

        ctx.obj = IsicContext(
            oauth=oauth,
            session=session,
            env=env,
            user=user,
            verbose=verbose,
        )


cli.add_command(accession_group, name='accession')
cli.add_command(collection_group, name='collection')
cli.add_command(image_group, name='image')
cli.add_command(metadata_group, name='metadata')
cli.add_command(user_group, name='user')


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

        ctx = get_current_context(silent=True)
        env = '-'
        user = '-'

        if ctx and ctx.obj:
            env = ctx.obj['env']

            if ctx.obj.user:
                user = ctx.obj.user['id']

        click.echo(f'isic-cli: v{get_version() or "-"}', err=True)
        click.echo(f'python:   v{platform.python_version()}', err=True)
        click.echo(f'time:     {datetime.utcnow().isoformat()}', err=True)
        click.echo(f'os:       {platform.platform()}', err=True)
        click.echo(f'env:      {env}', err=True)
        click.echo(f'user:     {user}', err=True)
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
