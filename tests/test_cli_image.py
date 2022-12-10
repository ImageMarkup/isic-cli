import os
from pathlib import Path

import pytest


@pytest.fixture
def outdir():
    return "somedir"


@pytest.fixture
def mock_images(mocker, isolated_filesystem, outdir):
    def _download_image_side_effect(*args, **kwargs):
        with open(Path(outdir) / "ISIC_0000000.JPG", "wb") as f:
            f.write(b"12345")

    mocker.patch("isic_cli.cli.image.get_num_images", return_value=1)
    mocker.patch(
        "isic_cli.cli.image.get_images",
        return_value=iter(
            [
                {
                    "isic_id": "ISIC_0000000",
                    "copyright_license": "CC-0",
                    "attribution": "\U00001F600 some-institution",
                    "metadata": {
                        "acquisition": {},
                        "clinical": {"sex": "male", "diagnosis": "melanoma"},
                    },
                }
            ]
        ),
    )
    mocker.patch("isic_cli.cli.image.download_image", side_effect=_download_image_side_effect)


def test_image_download(cli_run, isolated_filesystem, outdir, mock_images):
    result = cli_run(["image", "download", outdir])

    assert result.exit_code == 0, result.exception
    assert os.path.exists(f"{outdir}/ISIC_0000000.JPG")
    assert os.path.exists(f"{outdir}/metadata.csv")
    assert os.path.exists(f"{outdir}/attribution.txt")
