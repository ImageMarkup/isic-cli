from importlib.metadata import PackageNotFoundError, version
import logging
import sys
from typing import Optional

import click
from packaging.version import Version
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def get_version() -> Optional[Version]:
    try:
        return Version(version("isic-cli"))
    except PackageNotFoundError:
        # package is not installed
        return None


def is_dev_install():
    version = get_version()
    return not version or version.dev


def upgrade_type(from_version: Version, to_version: Version) -> Optional[str]:
    if to_version.major > from_version.major:
        return "major"
    elif to_version.minor > from_version.minor:
        return "minor"
    elif to_version.micro > from_version.micro:
        return "micro"


def _pypi_releases():
    r = requests.get("https://pypi.org/pypi/isic-cli/json", timeout=(5, 5))
    r.raise_for_status()
    return r.json()["releases"]


def newest_version_available() -> Optional[Version]:
    releases = [Version(v) for v in _pypi_releases().keys()]
    real_releases = [x for x in releases if not x.is_prerelease and not x.is_devrelease]
    if real_releases:
        return sorted(real_releases)[-1]


def check_for_newer_version():
    this_version = get_version()

    if not this_version or this_version.is_devrelease:
        return

    try:
        newest_version = newest_version_available()
    except RequestException:
        logger.warning("Failed to check for newer version of isic-cli.")
        return
    else:
        if not newest_version:
            return

        upgrade_type_available = upgrade_type(this_version, newest_version)

        if upgrade_type_available == "major":
            click.secho(
                """There is a new major version of isic-cli available.
You must upgrade before continuing. See https://github.com/ImageMarkup/isic-cli for instructions.
""",
                fg="yellow",
                err=True,
            )
            sys.exit(1)
        elif upgrade_type_available == "minor":
            click.secho(
                "Psst, there's a new version of isic-cli available. Upgrade!\n",
                fg="yellow",
                err=True,
            )
