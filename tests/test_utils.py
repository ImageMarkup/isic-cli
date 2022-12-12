import pytest

from isic_cli.cli.utils import get_attributions


@pytest.mark.parametrize(
    "images,attributions",
    [
        [
            [
                {"attribution": "foo"},
                {"attribution": "bar"},
                {"attribution": "foo"},
                {"attribution": "bar"},
            ],
            ["bar", "foo"],
        ],
        [
            [
                {"attribution": "foo"},
                {"attribution": "foo"},
                {"attribution": "bar"},
            ],
            ["foo", "bar"],
        ],
        [
            [
                {"attribution": "foo"},
                {"attribution": "foo"},
                {"attribution": "bar"},
                {"attribution": "Anonymous"},
            ],
            ["foo", "bar", "Anonymous"],
        ],
        [
            [
                {"attribution": "foo"},
                {"attribution": "foo"},
                {"attribution": "bar"},
                {"attribution": "Anonymous"},
                {"attribution": "Anonymous"},
                {"attribution": "Anonymous"},
            ],
            ["foo", "bar", "Anonymous"],
        ],
    ],
)
def test_get_attributions(images, attributions):
    assert get_attributions(images) == attributions
