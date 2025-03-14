from __future__ import annotations

from pathlib import Path
import re
import sys

import pytest
from pytest_lazy_fixtures import lf


@pytest.fixture()
def _mock_image_metadata(mocker):
    mocker.patch("isic_cli.cli.metadata.get_num_images", return_value=2)
    mocker.patch(
        "isic_cli.cli.metadata.get_images",
        return_value=iter(
            [
                {
                    "isic_id": "ISIC_0000000",
                    "attribution": "\U00001f600 Foo",
                    "copyright_license": "CC-0",
                    "metadata": {
                        "acquisition": {},
                        "clinical": {"sex": "male", "diagnosis": "melanoma"},
                    },
                },
                {
                    "isic_id": "ISIC_0000001",
                    "attribution": "\U00001f600 Bar",
                    "copyright_license": "CC-BY-NC",
                    "metadata": {
                        "acquisition": {},
                        "clinical": {"sex": "female", "diagnosis": "nevus"},
                    },
                },
            ]
        ),
    )


def test_metadata_validate(runner, cli_run):
    with runner.isolated_filesystem():
        with Path("foo.csv").open("w") as f:
            f.write("diagnosis,sex\nfoo,bar")

        result = cli_run(["metadata", "validate", "foo.csv"])

    assert result.exit_code == 1, result.exception
    assert re.search(r"Unsupported value for diagnosis: 'foo'.", result.output), result.output
    assert re.search(r"sex.*Input should be 'male' or 'female'", result.output), result.output


def test_metadata_validate_lesions_patients(runner, cli_run):
    with runner.isolated_filesystem():
        with Path("foo.csv").open("w") as f:
            f.write("lesion_id,patient_id\nl1,p1\nl1,p2")

        result = cli_run(["metadata", "validate", "foo.csv"])

    assert result.exit_code == 1, result.exception
    assert re.search(r"belong to multiple patients", result.output), result.output


@pytest.mark.usefixtures("_mock_image_metadata")
@pytest.mark.parametrize(
    "cli_runner",
    [lf("cli_run"), lf("cli_run_non_utf8")],
)
def test_metadata_download_stdout(cli_runner):
    result = cli_runner(["metadata", "download"])
    assert result.exit_code == 0, result.exception
    assert re.search(r"ISIC_0000000.*Foo.*CC-0.*melanoma.*male", result.output), result.output


@pytest.mark.usefixtures("_mock_image_metadata", "_isolated_filesystem")
@pytest.mark.parametrize(
    "cli_runner",
    [lf("cli_run"), lf("cli_run_non_utf8")],
)
def test_metadata_download_file(cli_runner):
    result = cli_runner(["metadata", "download", "-o", "foo.csv"])

    assert result.exit_code == 0, result.exception

    with Path("foo.csv").open() as f:
        output = f.read()

    assert re.search(r"ISIC_0000000.*Foo.*CC-0.*melanoma.*male", output), output


@pytest.mark.skipif(sys.platform == "win32", reason="Windows does not support this test")
@pytest.mark.usefixtures("_mock_image_metadata", "_isolated_filesystem")
def test_metadata_download_file_no_write(cli_run):
    result = cli_run(["metadata", "download", "-o", "/metadata.csv"])
    # it's important that the exit code is 2 and not 1, because the key constraint of this
    # functionality is that the user gets the error message before spending their time
    # downloading the data. exit code 2 is for usage errors with click.
    assert result.exit_code == 2, result.exception
    assert re.search(r"Permission denied", result.output), result.output


@pytest.mark.usefixtures("_mock_image_metadata", "_isolated_filesystem")
def test_metadata_download_file_bad_filename(cli_run):
    result = cli_run(["metadata", "download", "-o", f"{'1' * 255}.csv"])
    # see comment in test_metadata_download_file_no_write for why exit code is 2
    assert result.exit_code == 2, result.exception
    assert re.search(r"Cannot write to", result.output), result.output


@pytest.mark.usefixtures("_mock_image_metadata")
@pytest.mark.parametrize(
    "cli_runner",
    [lf("cli_run"), lf("cli_run_non_utf8")],
)
def test_metadata_download_newlines(cli_runner, mocker):
    result = cli_runner(["metadata", "download", "-o", "foo.csv"])

    assert result.exit_code == 0, result.exception

    with Path("foo.csv").open() as f:
        output = f.read()

    assert output.count("\n") == 3, output
