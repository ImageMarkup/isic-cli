import re

import click
from click.testing import CliRunner
import pytest
from requests.models import HTTPError

from isic_cli.cli.types import CollectionId


@pytest.mark.parametrize(
    "locked,locked_okay,expected_exit_code",
    [
        [True, False, 1],
        [True, True, 0],
        [False, False, 0],
        [False, True, 0],
    ],
)
def test_collection_id_type_locking(mocker, locked, locked_okay, expected_exit_code):
    @click.command()
    @click.argument("foo", type=CollectionId(locked_okay=locked_okay))
    def cmd(foo):
        pass

    mocker.patch(
        "isic_cli.cli.types.get_collection",
        return_value={
            "id": 1,
            "name": "foo",
            "public": True,
            "pinned": False,
            "locked": locked,
            "doi": None,
        },
    )

    # magicmock is used to mock out ctx.obj
    result = CliRunner().invoke(cmd, ["1"], obj=mocker.MagicMock())
    assert result.exit_code == expected_exit_code, result.exit_code

    if expected_exit_code == 1:
        assert "locked for modification" in result.output, result.output


def test_collection_id_type_access(mocker):
    @click.command()
    @click.argument("foo", type=CollectionId())
    def cmd(foo):
        pass

    def _raise_404(*args, **kwargs):
        raise HTTPError(response=mocker.MagicMock(status_code=404))

    mocker.patch("isic_cli.cli.types.get_collection", _raise_404)

    # magicmock is used to mock out ctx.obj
    result = CliRunner().invoke(cmd, ["1"], obj=mocker.MagicMock())
    assert result.exit_code == 2, result.exit_code
    assert "does not exist" in result.output, result.output


def test_collection_list(cli_run, mocker):
    mocker.patch(
        "isic_cli.cli.collection.get_collections",
        return_value=iter(
            [
                {
                    "id": 5,
                    "name": "foo",
                    "public": True,
                    "pinned": False,
                    "locked": True,
                    "doi": None,
                }
            ]
        ),
    )

    result = cli_run(["collection", "list"])

    assert result.exit_code == 0, result.exception
    assert re.search(r"5.*foo.*True.*False.*True", result.output), result.output


def test_collection_add_images(cli_run, mocker, mock_user):
    mocker.patch(
        "isic_cli.cli.types.get_collection",
        return_value={
            "id": 1,
            "name": "foo",
            "public": True,
            "pinned": False,
            "locked": False,
            "doi": None,
        },
    )
    mocker.patch(
        "isic_cli.cli.collection.bulk_collection_operation",
        return_value={
            "succeeded": ["ISIC_0000000"],
            "no_perms_or_does_not_exist": ["ISIC_1234567"],
            "private_image_public_collection": ["ISIC_1111111"],
        },
    )

    result = cli_run(
        ["collection", "add-images", "1", "--from-isic-ids", "-"],
        input="ISIC_1111111\nISIC_1234567",
    )

    assert result.exit_code == 0, (result.exception, result.output)
    assert re.search(r"Image added.*ISIC_0000000", result.output), result.output
