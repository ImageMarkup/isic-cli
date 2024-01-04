import re

import pytest


@pytest.fixture
def mock_image_metadata(mocker):
    mocker.patch("isic_cli.cli.metadata.get_num_images", return_value=1)
    mocker.patch(
        "isic_cli.cli.metadata.get_images",
        return_value=iter(
            [
                {
                    "isic_id": "ISIC_0000000",
                    "attribution": "\U00001F600 Foo",
                    "copyright_license": "CC-0",
                    "metadata": {
                        "acquisition": {},
                        "clinical": {"sex": "male", "diagnosis": "melanoma"},
                    },
                }
            ]
        ),
    )


def test_metadata_validate(runner, cli_run):
    with runner.isolated_filesystem():
        with open("foo.csv", "w") as f:
            f.write("diagnosis,sex\nfoo,bar")

        result = cli_run(["metadata", "validate", "foo.csv"])

    assert result.exit_code == 1, result.exception
    assert re.search(r"Unsupported value for diagnosis: 'foo'.", result.output), result.output
    assert re.search(r"sex.*Input should be 'male' or 'female'", result.output), result.output


def test_metadata_validate_lesions_patients(runner, cli_run):
    with runner.isolated_filesystem():
        with open("foo.csv", "w") as f:
            f.write("lesion_id,patient_id\nl1,p1\nl1,p2")

        result = cli_run(["metadata", "validate", "foo.csv"])

    assert result.exit_code == 1, result.exception
    assert re.search(r"belong to multiple patients", result.output), result.output


def test_metadata_download_stdout(cli_run, mock_image_metadata):
    result = cli_run(["metadata", "download"])
    assert result.exit_code == 0, result.exception
    assert re.search(r"ISIC_0000000.*Foo.*CC-0.*melanoma.*male", result.output), result.output


def test_metadata_download_file(cli_run, isolated_filesystem, mock_image_metadata):
    result = cli_run(["metadata", "download", "-o", "foo.csv"])

    assert result.exit_code == 0, result.exception

    with open("foo.csv", "r") as f:
        output = f.read()

    assert re.search(r"ISIC_0000000.*Foo.*CC-0.*melanoma.*male", output), output
