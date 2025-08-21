from __future__ import annotations

import atexit
from concurrent.futures import ThreadPoolExecutor
import csv
import functools
import itertools
import logging
import os
from pathlib import Path
import signal
import sys
from typing import TYPE_CHECKING

import click
from click.types import IntRange
from humanize import intcomma, naturalsize
from more_itertools.more import chunked
from rich.console import Console
from rich.progress import Progress

from isic_cli.cli.types import CommaSeparatedCollectionIds, SearchString
from isic_cli.cli.utils import _extract_metadata, get_attributions, suggest_guest_login
from isic_cli.io.http import (
    download_image,
    get_available_disk_space,
    get_images,
    get_license,
    get_num_images,
    get_size_images,
)

if TYPE_CHECKING:
    from isic_cli.cli.context import IsicContext


logger = logging.getLogger(__name__)


def cleanup_partially_downloaded_files(directory: Path) -> None:
    permission_errors = False
    for p in directory.glob(f"**/.isic-partial.{os.getpid()}.*"):
        # missing_ok=True because it's possible that another thread moved the temporary file to
        # its final destination after listing it but before unlinking.
        try:
            p.unlink(missing_ok=True)
        except PermissionError:  # noqa: PERF203
            # frequently on windows this is raised. it appears like this could be caused by
            # antivirus or various indexers that attempt to use the file shortly after it's
            # created.
            permission_errors = True

    if permission_errors:
        logger.warning(
            click.style(
                "Permission error while cleaning up one or more partially downloaded files",
                fg="yellow",
            )
        )


def _check_and_confirm_available_disk_space(outdir: Path, download_size: int) -> None:
    available_space = get_available_disk_space(outdir)

    if available_space is not None and download_size > available_space:
        nice_total_size = naturalsize(download_size)
        available_space_nice = naturalsize(available_space)
        click.echo()
        click.secho(
            "Warning: Insufficient disk space for download.",
            fg="yellow",
        )
        click.echo(f"Required: {nice_total_size}")
        click.echo(f"Available: {available_space_nice}")
        click.echo()
        if not click.confirm("Continue with download anyway?"):
            click.echo("Download cancelled.")
            sys.exit(0)


@click.group(short_help="Manage images.")
@click.pass_obj
def image(ctx):
    pass


@image.command(
    name="download", help="Download a set of images and metadata, optionally filtering results."
)
@click.option(
    "-s",
    "--search",
    type=SearchString(),
    default="",
    help="e.g. 'diagnosis_3:\"Melanoma Invasive\" AND age_approx:50'",
)
@click.option(
    "-c",
    "--collections",
    type=CommaSeparatedCollectionIds(),
    default="",
    help=(
        "Filter the images based on a comma separated string of collection"
        " ids (see isic collection list)."
    ),
)
@click.option(
    "-l",
    "--limit",
    default=0,
    metavar="INTEGER",
    type=IntRange(min=0),
    help="Download at most LIMIT images. Use a value of 0 to download all images.",
)
@click.argument(
    "outdir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
@click.pass_obj
@suggest_guest_login
def download(
    ctx: IsicContext,
    search: str,
    collections: str,
    limit: int,
    outdir: Path,
):
    """
    Download images from the ISIC Archive.

    The search query uses a simple DSL syntax.

    Some example queries are:

    age_approx:50 AND diagnosis_3:"Melanoma Invasive"

    age_approx:[20 TO 40] AND sex:male

    anatom_site_general:*torso AND image_type:dermoscopic
    """
    if not search and not collections and limit == 0:
        click.echo()
        click.secho(
            "Note: You're downloading the entire ISIC Archive without filters.",
            fg="yellow",
            bold=True,
        )
        click.echo(
            "A prebuilt snapshot of all public data is available for faster bulk access at:\n"
            "https://isic-archive.s3.us-east-1.amazonaws.com/snapshots/ISIC_images.zip"
        )
        click.echo()

    outdir.mkdir(parents=True, exist_ok=True)

    def signal_handler(signum, frame):
        cleanup_partially_downloaded_files(outdir)
        sys.exit(1)

    # remove partially downloaded files on exit
    atexit.register(cleanup_partially_downloaded_files, outdir)
    # also remove partially downloaded files on SIGINT/SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    archive_num_images = get_num_images(ctx.session, search, collections)
    download_num_images = archive_num_images if limit == 0 else min(archive_num_images, limit)
    nice_num_images = intcomma(download_num_images)

    # only show size information when downloading all images (no limit) because when
    # a limit is applied we can't accurately predict which specific images will be
    # downloaded.
    if limit == 0:
        archive_total_size = get_size_images(ctx.session, search, collections)
        nice_total_size = naturalsize(archive_total_size)
        _check_and_confirm_available_disk_space(outdir, archive_total_size)

    with Progress(console=Console(file=sys.stderr)) as progress:
        if limit == 0:
            message = f"Downloading images + metadata ({nice_num_images} files, {nice_total_size})"
        else:
            message = f"Downloading images + metadata ({nice_num_images} files)"

        task = progress.add_task(message, total=download_num_images)

        images_iterator = itertools.islice(
            get_images(ctx.session, search, collections), download_num_images
        )

        # See comment above _extract_metadata for why this is necessary
        images = []
        func = functools.partial(download_image, to=outdir, progress=progress, task=task)
        with ThreadPoolExecutor(max(10, os.cpu_count() or 10)) as thread_pool:
            for image_chunk in chunked(images_iterator, 100):
                images.extend(image_chunk)
                thread_pool.map(func, image_chunk)

        headers, records = _extract_metadata(images)
        with (outdir / "metadata.csv").open("w", newline="", encoding="utf8") as outfile:
            writer = csv.DictWriter(outfile, headers)
            writer.writeheader()
            writer.writerows(records)

        with (outdir / "attribution.txt").open("w", encoding="utf8") as outfile:
            # TODO: os.linesep?
            outfile.write("\n\n".join(get_attributions(records)))

        licenses = {record["copyright_license"] for record in records}
        (outdir / "licenses").mkdir(exist_ok=True)
        for license_type in licenses:
            with (outdir / "licenses" / f"{license_type}.txt").open("w") as outfile:
                outfile.write(get_license(ctx.session, license_type))

    click.echo()
    click.secho(f"Successfully downloaded {nice_num_images} images to {outdir}/.", fg="green")
    click.secho(
        f'Successfully wrote {nice_num_images} metadata records to {outdir / "metadata.csv"}.',
        fg="green",
    )
    click.secho(
        f'Successfully wrote attributions to {outdir / "attribution.txt"}.',
        fg="green",
    )
    click.secho(
        f'Successfully wrote {len(licenses)} license(s) to {outdir / "licenses"}.', fg="green"
    )
