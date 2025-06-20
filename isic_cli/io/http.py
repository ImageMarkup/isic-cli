from __future__ import annotations

import logging
import os
from pathlib import PurePosixPath
import shutil
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from more_itertools import chunked
from requests.exceptions import ChunkedEncodingError, ConnectionError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from isic_cli.session import IsicCliSession

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

logger = logging.getLogger("isic_cli")


def get_users_me(session: IsicCliSession) -> dict | None:
    r = session.get("users/me/")
    r.raise_for_status()
    return r.json()


def get_collection(session: IsicCliSession, collection_id: int | str) -> dict:
    r = session.get(f"collections/{collection_id}/")
    r.raise_for_status()
    return r.json()


def get_cohort(session: IsicCliSession, cohort_id: int | str) -> dict:
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

    ret.update({k: v for k, v in b.items() if k not in a})

    return ret


def bulk_collection_operation(  # noqa: PLR0913
    session: IsicCliSession,
    collection_id: int,
    operation: str,
    isic_ids: Iterable[str],
    progress,
    task,
) -> dict[str, list[str]]:
    results = {}

    for chunk in chunked(isic_ids, 50):
        r = session.post(f"collections/{collection_id}/{operation}/", json={"isic_ids": chunk})
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


def get_size_images(session: IsicCliSession, search: str = "", collections: str = "") -> int:
    """Get the total size in bytes of all images matching the search criteria."""
    params = {
        "query": search,
        "collections": collections,
    }
    r = session.get("images/search/size/", params=params)
    r.raise_for_status()
    return r.json()["size"]


def get_available_disk_space(path: Path) -> int | None:
    """
    Get available disk space in bytes for the given path.

    Returns None if unable to determine disk space (path doesn't exist or permission denied).
    """
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    else:
        logger.debug("Available disk space: %s bytes", usage.free)
        return usage.free


def get_license(session: IsicCliSession, license_type: str) -> str:
    r = session.get(f"zip-download/license-file/{license_type}/")
    r.raise_for_status()
    return r.text


# see https://github.com/danlamanna/retryable-requests/issues/10 to understand the
# scenario which requires additional retry logic.
@retry(
    retry=retry_if_exception_type((ConnectionError, ChunkedEncodingError)),
    wait=wait_exponential(multiplier=1, min=3, max=10),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)
def download_image(image: dict, to: Path, progress, task) -> None:
    url = image["files"]["full"]["url"]
    parsed_url = urlparse(url)
    path = parsed_url.path
    # defaulting to jpg is simply a convenience for development where the images
    # are extension-less since they come from a synthetic image generator.
    extension = PurePosixPath(path).suffix.lstrip(".") or "jpg"

    dest_path = to / f'{image["isic_id"]}.{extension}'

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
        with NamedTemporaryFile(
            dir=to, prefix=f".isic-partial.{os.getpid()}.", delete=False
        ) as outfile:
            temp_file_name = outfile.name
            for chunk in r.iter_content(1024 * 1024 * 5):
                outfile.write(chunk)

        shutil.move(temp_file_name, dest_path)

    progress.update(task, advance=1)
