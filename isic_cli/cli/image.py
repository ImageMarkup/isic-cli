import itertools
from pathlib import Path
import sys

import click
from click.types import IntRange
from humanize import intcomma
from joblib import Parallel, delayed, parallel_backend
from rich.console import Console
from rich.progress import Progress

from isic_cli.cli.context import IsicContext
from isic_cli.cli.types import SearchString
from isic_cli.cli.utils import suggest_guest_login
from isic_cli.io.http import download_image, get_images, get_num_images


@click.group(short_help='Manage images.')
@click.pass_obj
def image(ctx):
    pass


@image.command(
    name='download', help='Download a set of images and metadata, optionally filtering results.'
)
@click.option(
    '-s', '--search', type=SearchString(), help='e.g. "diagnosis:melanoma AND age_approx:50"'
)
@click.option(
    '-c',
    '--collections',
    default='',
    help=(
        'Limit the images based on a comma separated string of collection'
        ' ids (see isic collection list).'
    ),
)
@click.option(
    '-l',
    '--limit',
    default=1_000,
    metavar='INTEGER',
    type=IntRange(min=0),
    help='Use a value of 0 to disable the limit.',
)
@click.option(
    '-o',
    '--outdir',
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    default=Path('images'),
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

    age_approx:50 AND diagnosis:melanoma

    age_approx:[20 TO 40] AND sex:male

    anatom_site_general:*torso AND image_type:dermoscopic
    """
    outdir.mkdir(exist_ok=True)
    with Progress(console=Console(file=sys.stderr)) as progress:
        num_images = get_num_images(ctx.session, search, collections)
        if limit > 0:
            num_images = min(num_images, limit)

        task = progress.add_task(
            f'Downloading images ({intcomma( num_images )} total)', total=num_images
        )
        images = get_images(ctx.session, search, collections)

        if limit > 0:
            images = itertools.islice(images, limit)

        with parallel_backend('threading'):
            Parallel()(delayed(download_image)(image, outdir, progress, task) for image in images)
