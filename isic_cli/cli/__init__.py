from datetime import datetime
from http.client import HTTPConnection
import logging
import os
import platform
import sys
import traceback

from authlib.integrations.base_client.errors import OAuthError
import click
from click import UsageError, get_current_context
from requests.exceptions import HTTPError
import sentry_sdk
from sentry_sdk import capture_exception
from sentry_sdk.api import set_context, set_tag
from sentry_sdk.integrations.argv import ArgvIntegration
from sentry_sdk.integrations.atexit import AtexitIntegration
from sentry_sdk.integrations.dedupe import DedupeIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.modules import ModulesIntegration
from sentry_sdk.integrations.stdlib import StdlibIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

from isic_cli.cli.accession import accession as accession_group
from isic_cli.cli.collection import collection as collection_group
from isic_cli.cli.context import IsicContext
from isic_cli.cli.image import image as image_group
from isic_cli.cli.metadata import metadata as metadata_group
from isic_cli.cli.user import user as user_group
from isic_cli.io.http import get_users_me
from isic_cli.oauth import get_oauth_client
from isic_cli.session import get_session
from isic_cli.utils.version import check_for_newer_version, get_version, is_dev_install

DOMAINS = {
    "dev": "http://127.0.0.1:8000",
    "sandbox": "https://api-sandbox.isic-archive.com",
    "prod": "https://api.isic-archive.com",
}

SENTRY_DSN = "https://3c3afa5c12e04042979583df1a07abd2@o267860.ingest.sentry.io/6645383"

logger = logging.getLogger("isic_cli")


# overrides sentry_sdk.integrations.atexit.default_callback
def _sentry_atexit_display(pending: int, timeout: int) -> None:
    quit_char = f'Ctrl-{os.name == "nt" and "Break" or "C"}'
    click.echo(f"Sending bug report. Press {quit_char} to quit.", err=True)
    sys.stderr.flush()


def _sentry_setup():
    if not is_dev_install():
        sentry_sdk.init(
            SENTRY_DSN,
            release=str(get_version()),
            # debug=True,
            environment="production",
            traces_sample_rate=0,
            in_app_include=["isic_cli"],
            # use the set of default integrations minus the Excepthook. this is because we only
            # want to track sentry issues manually to avoid telemetry that hasn't been consented to.
            # https://docs.sentry.io/platforms/python/configuration/integrations/default-integrations
            default_integrations=False,
            integrations=[
                AtexitIntegration(callback=_sentry_atexit_display),
                DedupeIntegration(),
                StdlibIntegration(),
                ModulesIntegration(),
                ArgvIntegration(),
                # set event_level to None so log messages will never create sentry issues,
                # only breadcrumbs.
                LoggingIntegration(event_level=None),
                ThreadingIntegration(),
            ],
        )


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
@click.option(
    "--guest", is_flag=True, default=False, help="Simulate a non logged in user.", hidden=True
)
@click.option(
    "--sandbox",
    is_flag=True,
    default=False,
    help="Execute against the ISIC Archive sandbox.",
    hidden=True,
    envvar="ISIC_SANDBOX",
)
@click.option(
    "--dev",
    is_flag=True,
    default=False,
    help="Execute against a dev ISIC Archive environment.",
    hidden=True,
    envvar="ISIC_DEV",
)
@click.option(
    "--no-version-check",
    is_flag=True,
    default=False,
    help="Disable the version upgrade check.",
    hidden=True,
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose mode.")
@click.version_option()
@click.pass_context
def cli(ctx, verbose: bool, guest: bool, sandbox: bool, dev: bool, no_version_check: bool):
    logger.addHandler(logging.StreamHandler(sys.stderr))
    logger.setLevel(logging.WARN)

    if verbose:
        HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.addHandler(logging.StreamHandler(sys.stderr))
        requests_log.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    if sandbox and dev:
        raise UsageError("Illegal usage: --sandbox is mutually exclusive with --dev.")

    env = "prod"
    if sandbox:
        env = "sandbox"
    elif dev:
        env = "dev"

    _sentry_setup()

    if no_version_check:
        logger.warning("Disabling the version check could cause errors.")
    else:
        check_for_newer_version()

    oauth = get_oauth_client(f"{DOMAINS[env]}/oauth")

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
                "Something went wrong with restoring a login, you may need to log back in.",
                fg="yellow",
            )

    with get_session(f"{DOMAINS[env]}/api/v2/", oauth.auth_headers) as session:
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


cli.add_command(accession_group, name="accession")
cli.add_command(collection_group, name="collection")
cli.add_command(image_group, name="image")
cli.add_command(metadata_group, name="metadata")
cli.add_command(user_group, name="user")


def main():
    try:
        cli()
    except Exception as e:
        click.echo(
            click.style(
                "The following unexpected error occurred while attempting your operation:\n",
                fg="red",
            ),
            err=True,
        )

        click.echo(traceback.format_exc(), err=True)

        ctx = get_current_context(silent=True)
        env = "-"
        user = "-"

        if ctx and ctx.obj:
            env = ctx.obj["env"]

            if ctx.obj.user:
                user = ctx.obj.user["id"]

        set_tag("platform", platform.system())
        set_tag("isic-env", env)
        set_context("operating system", {"name": platform.platform()})
        set_context("user", {"id": user})

        click.echo(f'isic-cli: v{get_version() or "-"}', err=True)
        click.echo(f"python:   v{platform.python_version()}", err=True)
        click.echo(f"time:     {datetime.utcnow().isoformat()}", err=True)
        click.echo(f"os:       {platform.platform()}", err=True)
        click.echo(f"env:      {env}", err=True)
        click.echo(f"user:     {user}", err=True)
        click.echo(f'command:  isic {" ".join(sys.argv[1:])}\n', err=True)

        if is_dev_install():
            return

        send_bug_report = click.prompt(
            click.style(
                "This is a bug in isic-cli, would you like to send a bug report?", fg="yellow"
            ),
            type=click.Choice(choices=["y", "n"]),
            default="y",
            err=True,
            show_choices=True,
        )

        # this is the only code that actually sends data to sentry, so it's guarded with an opt-in
        if send_bug_report == "y":
            capture_exception(e)
        else:
            click.secho("Alternatively you can open an issue below: \n", fg="yellow", err=True)
            click.echo("https://github.com/ImageMarkup/isic-cli/issues/new", err=True)
