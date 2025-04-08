from __future__ import annotations

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


class CommaSeparatedIdentifiers(click.ParamType):
    name = "comma_separated_identifiers"

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)

        if value != "" and not re.match(r"^(\d+)(,\d+)*$", value):
            self.fail(f'Improperly formatted value "{value}".', param, ctx)
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
                    f"Collection {value} does not exist or you don't have access to it.", param, ctx
                )
            else:
                raise

        if collection["locked"] and not self.locked_okay:
            click.secho(f'"{collection["name"]}" is locked for modifications.', err=True, fg="red")
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
                    f"Cohort {value} does not exist or you don't have access to it.", param, ctx
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

        # writeable checks on click.Path only apply to already existing paths, see
        # https://github.com/pallets/click/issues/2495.
        # check if the final path is writable before going to the effort of downloading the data.
        if value is not None and str(value) != "-":
            try:
                value.parent.mkdir(parents=True, exist_ok=True)
                with value.open("w", newline="", encoding="utf8"):
                    pass
            except PermissionError:
                self.fail(f"Permission denied - cannot write to '{value}'.", param, ctx)
            except OSError as e:
                # this is a general catch-all for weirder issues like a read only filesystem,
                # filenames that are too long or have invalid chars, etc.
                self.fail(f"Cannot write to '{value}'. {e!s}", param, ctx)

        return value
