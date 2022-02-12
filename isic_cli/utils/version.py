from importlib.metadata import PackageNotFoundError, version
import sys

import click
from pkg_resources import parse_version
import requests
from requests.exceptions import RequestException


def get_version():
    try:
        v = version('isic-cli')
        if v == '0.0.0':  # TODO: this only occurs in testing.
            return None
    except PackageNotFoundError:
        # package is not installed
        return None


def newer_version_available():
    version = get_version()
    if version is None:
        return False

    this_version = parse_version(version)
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
            click.echo(
                click.style(
                    """There is a newer version of isic-cli available.
You must upgrade to the latest version before continuing.
If you are using pip, then you can upgrade by running the following command:
""",
                    fg='yellow',
                ),
                err=True,
            )
            click.echo(click.style('pip install --upgrade isic-cli', fg='green'), err=True)
            sys.exit(1)
    except RequestException:
        click.echo(
            click.style('Failed to check for newer version of isic-cli:', fg='red'), err=True
        )
        raise
