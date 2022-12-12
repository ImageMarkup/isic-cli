from collections.abc import Iterable
import logging
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
from typing import Optional, Union

from more_itertools import chunked
from requests.exceptions import ConnectionError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from isic_cli.session import IsicCliSession

logger = logging.getLogger("isic_cli")


def get_users_me(session: IsicCliSession) -> Optional[dict]:
    r = session.get("users/me/")
    r.raise_for_status()
    return r.json()


def get_collection(session: IsicCliSession, collection_id: Union[int, str]) -> dict:
    r = session.get(f"collections/{collection_id}/")
    r.raise_for_status()
    return r.json()


def get_cohort(session: IsicCliSession, cohort_id: Union[int, str]) -> dict:
    r = session.get(f"cohorts/{cohort_id}/")
    r.raise_for_status()
    return r.json()


def create_accession(session: IsicCliSession, cohort_id: int, original_blob: str) -> dict:
    r = session.post("accessions/", json={"original_blob": original_blob, "cohort": cohort_id})
    r.raise_for_status()
    return r.json()


def get_collections(session: IsicCliSession) -> Iterable[dict]:
    next_page = "collections/"

    while next_page:
        r = session.get(next_page)
        r.raise_for_status()
        yield from r.json()["results"]
        next_page = r.json()["next"]


def _merge_summaries(a: dict[str, list[str]], b: dict[str, list[str]]) -> dict[str, list[str]]:
    ret = {}
    for k, v in a.items():
        ret[k] = v + b.get(k, [])

    for k, v in b.items():
        if k not in a:
            ret[k] = v

    return ret


def bulk_collection_operation(
    session: IsicCliSession,
    collection_id: int,
    operation: str,
    isic_ids: Iterable[str],
    progress,
    task,
) -> dict[str, list[str]]:
    results = {}

    for chunk in chunked(isic_ids, 50):
        r = session.post(f"collections/{collection_id}/{operation}/", {"isic_ids": chunk})
        r.raise_for_status()

        results = _merge_summaries(results, r.json())

        progress.update(task, advance=len(chunk))

    return results


def get_images(session: IsicCliSession, search: str = "", collections: str = "") -> Iterable[dict]:
    next_page = f"images/search/?query={search}&collections={collections}"

    while next_page:
        r = session.get(next_page)
        r.raise_for_status()
        yield from r.json()["results"]
        next_page = r.json()["next"]


def get_num_images(session: IsicCliSession, search: str = "", collections: str = "") -> int:
    params = {
        "query": search,
        "collections": collections,
        "limit": 1,
    }
    r = session.get("images/search/", params=params)
    r.raise_for_status()
    return r.json()["count"]


# see https://github.com/danlamanna/retryable-requests/issues/10 to understand the
# scenario which requires additional retry logic.
@retry(
    retry=retry_if_exception_type(ConnectionError),
    wait=wait_exponential(multiplier=1, min=3, max=10),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)
def download_image(image: dict, to: Path, progress, task) -> None:
    dest_path = to / f'{image["isic_id"]}.JPG'

    # Avoid re downloading the image if one of the same name/size exists. This is a decent
    # enough proxy for detecting file differences without going through a hashing mechanism.
    if dest_path.exists() and dest_path.stat().st_size == image["files"]["full"]["size"]:
        progress.update(task, advance=1)
        return

    # intentionally omit auth headers, since these are s3 signed urls that already contain
    # credentials.
    with IsicCliSession() as session:
        r = session.get(image["files"]["full"]["url"], stream=True)
        r.raise_for_status()

        temp_file_name = None
        with NamedTemporaryFile(dir=to, prefix=".isic-partial.", delete=False) as outfile:
            temp_file_name = outfile.name
            for chunk in r.iter_content(1024 * 1024 * 5):
                outfile.write(chunk)

        shutil.move(temp_file_name, dest_path)

    progress.update(task, advance=1)
