import itertools
import json
from pathlib import Path
import sys

from joblib import Parallel, delayed, parallel_backend
from requests.exceptions import HTTPError
from rich.progress import Progress
import typer

from isic_cli.session import get_session
from isic_cli.utils import get_images, get_num_images

image = typer.Typer()


def _download_image(image: dict, to: Path, progress, task) -> None:
    # intentionally don't pass auth headers, since these are s3 signed urls that
    # already contain credentials.
    with get_session() as session:
        r = session.get(image['urls']['full'], stream=True)
        r.raise_for_status()

        with open(to / f'{image["isic_id"]}.JPG', 'wb') as outfile:
            for chunk in r.iter_content(1024 * 1024 * 5):
                outfile.write(chunk)
                # progress.update(task, advance=len(chunk))

        with open(to / f'{image["isic_id"]}.json', 'w') as outfile:
            del image['urls']
            json.dump(image, outfile, indent=2)

    progress.update(task, advance=1)


@image.command(name='download')
def download_images(
    ctx: typer.Context,
    search: str = typer.Option(''),
    collections: str = typer.Option(
        '',
        help='Limit the images based on a comma separated string of collection ids (see isic collection list).',  # noqa: E501
    ),
    max_images: int = typer.Option(1_000, min=0, help='Use a value of 0 to disable the limit.'),
    outdir: Path = typer.Option(Path('images'), file_okay=False, dir_okay=True, writable=True),
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
    with Progress() as progress:
        with get_session(ctx.obj.auth_headers) as session:
            num_images = get_num_images(session, search, collections)
            if max_images > 0:
                num_images = min(num_images, max_images)

            task = progress.add_task(f'Downloading images ({num_images} total)', total=num_images)
            images = get_images(session, search, collections)

            if max_images > 0:
                images = itertools.islice(images, max_images)

            try:
                with parallel_backend('threading'):
                    Parallel()(
                        delayed(_download_image)(image, outdir, progress, task) for image in images
                    )
            except HTTPError as e:
                if e.response.status_code == 400 and 'query' in e.response.json():
                    typer.echo('\n')
                    typer.secho(
                        'The search query is invalid, please see --help for info.',
                        fg=typer.colors.YELLOW,
                        err=True,
                        nl=False,
                    )
                    sys.exit(1)
                else:
                    raise
