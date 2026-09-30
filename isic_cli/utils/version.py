from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import logging
import sys

import click
from packaging.utils import parse_sdist_filename, parse_wheel_filename
from packaging.version import Version
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def get_version() -> Version | None:
    try:
        return Version(version("isic-cli"))
    except PackageNotFoundError:
        # package is not installed
        return None


def is_dev_install():
    version = get_version()
    return not version or version.is_devrelease


def upgrade_type(from_version: Version, to_version: Version) -> str | None:
    if to_version <= from_version:
        return None
    if to_version.major > from_version.major:
        return "major"
    if to_version.minor > from_version.minor:
        return "minor"
    if to_version.micro > from_version.micro:
        return "micro"


def _pypi_files() -> list[dict]:
    # https://peps.python.org/pep-0691/
    r = requests.get(
        "https://pypi.org/simple/isic-cli/",
        headers={"Accept": "application/vnd.pypi.simple.v1+json"},
        timeout=(5, 5),
    )
    r.raise_for_status()
    return r.json()["files"]


def _file_version(filename: str) -> Version:
    if filename.endswith(".whl"):
        return parse_wheel_filename(filename)[1]
    return parse_sdist_filename(filename)[1]


def newest_version_available() -> Version | None:
    releases = [
        _file_version(file["filename"])
        for file in _pypi_files()
        # yanked is optional, and is either a boolean or the reason the file was yanked
        if not file.get("yanked")
    ]
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
