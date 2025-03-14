from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def outdir():
    return "somedir"


@pytest.fixture()
def _mock_images(mocker, _isolated_filesystem, outdir):
    def _download_image_side_effect(*args, **kwargs):
        with (Path(outdir) / "ISIC_0000000.jpg").open("wb") as f:
            f.write(b"12345")

    mocker.patch("isic_cli.cli.image.get_num_images", return_value=1)
    mocker.patch(
        "isic_cli.cli.image.get_images",
        return_value=iter(
            [
                {
                    "isic_id": "ISIC_0000000",
                    "copyright_license": "CC-0",
                    "attribution": "\U00001f600 some-institution",
                    "metadata": {
                        "acquisition": {},
                        "clinical": {"sex": "male", "diagnosis": "melanoma"},
                    },
                }
            ]
        ),
    )
    mocker.patch("isic_cli.cli.image.download_image", side_effect=_download_image_side_effect)


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download(cli_run, outdir):
    result = cli_run(["image", "download", outdir])

    assert result.exit_code == 0, result.exception
    assert Path(f"{outdir}/ISIC_0000000.jpg").exists()
    assert Path(f"{outdir}/metadata.csv").exists()
    assert Path(f"{outdir}/attribution.txt").exists()
    assert Path(f"{outdir}/licenses/CC-0.txt").exists()


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_metadata_newlines(cli_run, outdir):
    result = cli_run(["image", "download", outdir])

    assert result.exit_code == 0, result.exception
    with Path(f"{outdir}/metadata.csv").open() as f:
        assert f.read().count("\n") == 2


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_cleanup_on_interrupt(mocker, outdir):
    from click.testing import CliRunner  # noqa: I001
    from isic_cli.cli import cli

    partial_file = Path(outdir) / ".isic-partial.ISIC_0000000.jpg"
    partial_file.parent.mkdir(parents=True)

    runner = CliRunner()

    cleanup = MagicMock(side_effect=KeyboardInterrupt)
    mocker.patch("isic_cli.cli.image.get_num_images", cleanup)

    result = runner.invoke(cli, ["image", "download", outdir], standalone_mode=False)

    assert cleanup.called
    assert result.exit_code == 1
    assert isinstance(result.exception.__cause__, KeyboardInterrupt)

    assert not partial_file.exists()
