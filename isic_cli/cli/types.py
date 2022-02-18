import re

import click
from click.types import IntParamType


class SearchString(click.ParamType):
    name = 'search_string'

    def convert(self, value, param, ctx):
        r = ctx.obj.session.get('images/search/', params={'query': value, 'limit': 1})
        if r.status_code == 400 and 'query' in r.json():
            self.fail('Invalid search query string "%s"' % value, param, ctx)
        return value


class CommaSeparatedIdentifiers(click.ParamType):
    name = 'comma_separated_identifiers'

    def convert(self, value, param, ctx):
        if not re.match(r'^(\d+)(,\d+)*$', value):
            self.fail('Improperly formatted value "%s".' % value, param, ctx)
        return value


class CollectionId(IntParamType):
    name = 'collection_id'

    def convert(self, value, param, ctx):
        r = ctx.obj.session.get(f'collections/{value}/')
        if not r.ok:
            self.fail(
                f"Collection {value} does not exist or you don't have access to it.", param, ctx
            )
        return value
