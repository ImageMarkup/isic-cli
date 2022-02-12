import json
from pathlib import Path
from typing import Iterable, Optional

from isic_cli.session import IsicCliSession, get_session


def get_collections(session: IsicCliSession) -> Iterable[dict]:
    next_page = 'collections?limit=1'

    while next_page:
        r = session.get(next_page)
        r.raise_for_status()
        yield from r.json()['results']
        next_page = r.json()['next']


def get_images(
    session: IsicCliSession, search: Optional[str] = None, collections: Optional[str] = None
) -> Iterable[dict]:
    next_page = (
        f'images/search/?query={search if search else ""}'
        + f'&collections={collections if collections else ""}'
    )

    while next_page:
        r = session.get(next_page)
        r.raise_for_status()
        yield from r.json()['results']
        next_page = r.json()['next']


def get_num_images(
    session: IsicCliSession, search: Optional[str] = None, collections: Optional[str] = None
) -> int:
    params = {
        'query': search if search else '',
        'collections': collections if collections else '',
        'limit': 1,
    }
    r = session.get('images/search/', params=params)
    r.raise_for_status()
    return r.json()['count']


def download_image(image: dict, to: Path, progress, task) -> None:
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
