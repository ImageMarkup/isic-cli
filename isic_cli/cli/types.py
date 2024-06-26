from __future__ import annotations

import re
import sys

import click
from click.types import IntParamType
from requests.models import HTTPError

from isic_cli.io.http import get_cohort, get_collection


class SearchString(click.ParamType):
    name = "search_string"

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)

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
