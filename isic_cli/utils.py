from typing import Iterable

from isic_cli.session import IsicCliSession


def get_collections(session: IsicCliSession) -> Iterable[dict]:
    next_page = 'collections?limit=1'

    while next_page:
        r = session.get(next_page)
        r.raise_for_status()
        yield from r.json()['results']
        next_page = r.json()['next']


def get_images(session: IsicCliSession, search: str, collections: str) -> Iterable[dict]:
    next_page = f'images/search/?query={search}' + f'&collections={collections}'

    while next_page:
        r = session.get(next_page)
        r.raise_for_status()
        yield from r.json()['results']
        next_page = r.json()['next']


def get_num_images(session: IsicCliSession, search: str, collections: str) -> int:
    params = {
        'query': search,
        'collections': collections,
        'limit': 1,
    }
    r = session.get('images/search/', params=params)
    r.raise_for_status()
    return r.json()['count']
