from __future__ import annotations

import contextlib
import re
import sys

import click
from click.types import IntParamType
from requests.models import HTTPError

from isic_cli.io.http import get_cohort, get_collection

unsupported_diagnosis_message = (
    "\n\nThe 'diagnosis' search filter is no longer supported.\n"
    "ISIC now uses a hierarchical taxonomy with diagnosis_1-5 fields.\n"
    "\n"
    "Example conversion:\n"
    "  Old: 'diagnosis:melanoma'\n"
    "  New: 'diagnosis_2:\"Malignant melanocytic proliferations (Melanoma)\"'\n"
    "\n"
    "For the complete taxonomy, refer to the ISIC Data Dictionary: https://www.isic-archive.com/data-dictionary"
)


class SearchString(click.ParamType):
    name = "search_string"

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)

        if "diagnosis:" in value:
            self.fail(click.style(unsupported_diagnosis_message, fg="yellow"), param, ctx)

        r = ctx.obj.session.get("images/search/", params={"query": value, "limit": 1})
        if r.status_code == 400 and "message" in r.json() and "query" in r.json()["message"]:
            self.fail(f'Invalid search query string "{value}"', param, ctx)
        return value


class CommaSeparatedCollectionIds(click.ParamType):
    name = "comma_separated_collection_ids"

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)

        if value != "" and not re.match(r"^(\d+)(,\d+)*$", value):
            self.fail(f'Improperly formatted value "{value}".', param, ctx)

        collection_ids = value.split(",") if value else []

        for collection_id in collection_ids:
            try:
                get_collection(ctx.obj.session, collection_id)
            except HTTPError as e:
                if e.response.status_code == 404:
                    append = ""
                    if not ctx.obj.user:
                        append = "Logging in may help (see `isic user login`)."

                    self.fail(
                        f"Collection {collection_id} does not exist or you don't have access to it. {append}",  # noqa: E501
                        param,
                        ctx,
                    )
                else:
                    raise

        return value


class CollectionId(IntParamType):
    name = "collection_id"

    def __init__(self, *, locked_okay: bool | None = False) -> None:
        super().__init__()
        self.locked_okay = locked_okay

    def convert(self, value: str, param, ctx) -> str:
        value = super().convert(value, param, ctx)

        try:
            collection = get_collection(ctx.obj.session, value)
        except HTTPError as e:
            if e.response.status_code == 404:
                self.fail(
                    f"Collection {value} does not exist or you don't have access to it.",
                    param,
                    ctx,
                )
            else:
                raise

        if collection["locked"] and not self.locked_okay:
            click.secho(
                f'"{collection["name"]}" is locked for modifications.',
                err=True,
                fg="red",
            )
            sys.exit(1)

        return value


class CohortId(IntParamType):
    name = "cohort_id"

    def convert(self, value: str, param, ctx) -> str:
        value = super().convert(value, param, ctx)

        try:
            get_cohort(ctx.obj.session, value)
        except HTTPError as e:
            if e.response.status_code == 404:
                self.fail(
                    f"Cohort {value} does not exist or you don't have access to it.",
                    param,
                    ctx,
                )
            else:
                raise

        return value


class WritableFilePath(click.Path):
    name = "writable_file_path"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.file_okay:
            raise ValueError("file_okay must be True")
        elif self.dir_okay:
            raise ValueError("dir_okay must be False")

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)

        # click.Path(writable=True) only validates existing paths, so it can't catch
        # the case where the file must be created. See
        # https://github.com/pallets/click/issues/2495. Attempt to open the file so we
        # exercise the real OS check, then remove it so this stays a pure probe —
        # a subsequent argument failing to parse must not leave a stray file behind.
        # The callback recreates it for real.
        #
        # Actually performing the operation is more reliable than heuristics like
        # os.access, which only checks POSIX mode bits and misses ACLs, read-only
        # mounts, immutable flags, etc. — it can say "writable" for a path the
        # kernel will still reject. If we want to know whether the write will work,
        # the most truthful test is to try it.
        if value is not None and str(value) != "-":
            try:
                # .exists() can itself raise (e.g. a filename that's too long), so
                # it has to live inside the try alongside the write probe.
                existed_before = value.exists()
                value.parent.mkdir(parents=True, exist_ok=True)
                with value.open("w", newline="", encoding="utf8"):
                    pass
            except OSError as e:
                msg = f"Permission denied - cannot write to '{value}': {e.strerror}."
                self.fail(msg, param, ctx)

            # remove what we created — a later argument could still fail to parse
            if not existed_before:
                with contextlib.suppress(OSError):
                    value.unlink()

        return value


class WritableDirectoryPath(click.Path):
    name = "writable_directory_path"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.file_okay:
            raise ValueError("file_okay must be False")
        elif not self.dir_okay:
            raise ValueError("dir_okay must be True")

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)

        # click.Path(writable=True) only validates existing paths, so it can't catch
        # the case where the directory must be created. See
        # https://github.com/pallets/click/issues/2495. Attempt the mkdir so we
        # exercise the real OS check, then remove it so this stays a pure probe —
        # a subsequent argument failing to parse must not leave a stray directory
        # behind. The callback recreates it for real.
        #
        # Actually performing the operation is more reliable than heuristics like
        # os.access, which only checks POSIX mode bits and misses ACLs, read-only
        # mounts, immutable flags, etc. — it can say "writable" for a path the
        # kernel will still reject. If we want to know whether mkdir will work,
        # the most truthful test is to try it.
        if value is not None:
            try:
                # .exists() can itself raise (e.g. a filename that's too long), so
                # it has to live inside the try alongside the write probe.
                existed_before = value.exists()
                value.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                msg = f"Permission denied - cannot write to '{value}': {e.strerror}."
                self.fail(msg, param, ctx)

            # remove what we created — a later argument could still fail to parse
            if not existed_before:
                with contextlib.suppress(OSError):
                    value.rmdir()

        return value
