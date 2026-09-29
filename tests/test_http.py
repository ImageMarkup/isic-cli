from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from isic_cli.io.http import get_images


def test_get_images_encodes_search(mocker):
    session = mocker.MagicMock()
    session.get.return_value.json.return_value = {"results": [], "next": None}
    search = 'attribution:"Foo & Bar" AND age_approx:[5 TO 25] AND sex:male+'

    list(get_images(session, search=search, collections="1,2"))

    url = session.get.call_args.args[0]
    assert parse_qs(urlparse(url).query) == {"query": [search], "collections": ["1,2"]}
