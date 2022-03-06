import csv
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
from isic_cli.cli.utils import _extract_metadata, get_attributions, suggest_guest_login
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
@click.argument(
    'outdir',
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

    age_approx:50 AND diagnosis:melanoma

    age_approx:[20 TO 40] AND sex:male

    anatom_site_general:*torso AND image_type:dermoscopic
    """
    outdir.mkdir(exist_ok=True)

    with Progress(console=Console(file=sys.stderr)) as progress:
        archive_num_images = get_num_images(ctx.session, search, collections)
        download_num_images = archive_num_images if limit == 0 else min(archive_num_images, limit)
        nice_num_images = intcomma(download_num_images)

        task1 = progress.add_task(
            f'Downloading image information ({nice_num_images} total)',
            total=download_num_images,
        )
        task2 = progress.add_task(
            f'Downloading image files ({nice_num_images} total)', total=download_num_images
        )
        images_iterator = itertools.islice(
            get_images(ctx.session, search, collections), download_num_images
        )
        images = []

        # See comment above _extract_metadata for why this is necessary
        for image in images_iterator:
            images.append(image)
            progress.update(task1, advance=1)

        with parallel_backend('threading'):
            Parallel()(delayed(download_image)(image, outdir, progress, task2) for image in images)

        headers, records = _extract_metadata(images)
        with (outdir / 'metadata.csv').open('w') as outfile:
            writer = csv.DictWriter(outfile, headers)
            writer.writeheader()
            writer.writerows(records)

        with (outdir / 'attribution.txt').open('w') as outfile:
            # TODO: os.linesep?
            outfile.write('\n\n'.join(get_attributions(records)))

    click.echo()
    click.secho(f'Successfully downloaded {nice_num_images} images to {outdir}/.', fg='green')
    click.secho(
        f'Successfully wrote {nice_num_images} metadata records to {outdir/"metadata.csv"}.',
        fg='green',
    )
    click.secho(
        f'Successfully wrote attributions to {outdir/"attribution.txt"}.',
        fg='green',
    )
