from typing import Iterable

from isic_cli.session import IsicCliSession


def get_images(session: IsicCliSession, search: str) -> Iterable[dict]:
    next_page = f'images/search/?query={search}'

    while next_page:
        r = session.get(next_page)
        r.raise_for_status()
        yield from r.json()['results']
        next_page = r.json()['next']


def get_num_images(session: IsicCliSession, search: str) -> int:
    r = session.get(f'images/search/?query={search}&limit=1')
    r.raise_for_status()
    return r.json()['count']
