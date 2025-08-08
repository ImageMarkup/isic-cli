from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from requests import HTTPError

from isic_cli.cli.image import cleanup_partially_downloaded_files


@pytest.fixture()
def outdir():
    return "somedir"


@pytest.fixture()
def _mock_images(mocker, _isolated_filesystem, outdir):
    def _download_image_side_effect(*args, **kwargs):
        with (Path(outdir) / "ISIC_0000000.jpg").open("wb") as f:
            f.write(b"12345")

    mocker.patch("isic_cli.cli.image.get_num_images", return_value=1)
    mocker.patch("isic_cli.cli.image.get_size_images", return_value=2e6)
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
def test_image_download_no_collection(mocker, cli_run, outdir):
    mocker.patch(
        "isic_cli.cli.types.get_collection",
        side_effect=HTTPError(response=mocker.MagicMock(status_code=404)),
    )

    result = cli_run(["image", "download", outdir, "--collections", "462"])

    assert result.exit_code == 2, result.exception
    assert "does not exist or you don't have access to it." in result.output


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_metadata_newlines(cli_run, outdir):
    result = cli_run(["image", "download", outdir])

    assert result.exit_code == 0, result.exception
    with Path(f"{outdir}/metadata.csv").open() as f:
        assert f.read().count("\n") == 2


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_cleanup(cli_run, outdir):
    partial_file = Path(outdir) / f".isic-partial.{os.getpid()}.ISIC_0000000.jpg"
    partial_file.parent.mkdir(parents=True)
    partial_file.touch()

    result = cli_run(["image", "download", outdir])
    assert result.exit_code == 0

    # this is run via atexit, but we want to test it here since we can't
    # easily test running the command in a subprocess.
    assert partial_file.exists()
    cleanup_partially_downloaded_files(Path(outdir))
    assert not partial_file.exists()


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_cleanup_permission_error(cli_run, outdir, mocker, caplog):
    partial_file = Path(outdir) / f".isic-partial.{os.getpid()}.ISIC_0000000.jpg"
    partial_file.parent.mkdir(parents=True)
    partial_file.touch()

    original_unlink = Path.unlink

    def mock_unlink(self, *, missing_ok=False):
        if str(partial_file) == str(self):
            raise PermissionError("Access is denied")
        return original_unlink(self, missing_ok=missing_ok)

    mocker.patch.object(Path, "unlink", mock_unlink)
    caplog.set_level(logging.WARNING)

    result = cli_run(["image", "download", outdir])
    assert result.exit_code == 0

    # run manually since atexit won't run in the test environment
    cleanup_partially_downloaded_files(Path(outdir))

    assert (
        "Permission error while cleaning up one or more partially downloaded files" in caplog.text
    )


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_legacy_diagnosis_unsupported(cli_run, outdir):
    result = cli_run(["image", "download", outdir, "--search", "diagnosis:melanoma"])
    assert result.exit_code == 2
    assert "no longer supported" in result.output


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_shows_size_info(cli_run, outdir):
    result = cli_run(["image", "download", outdir])
    assert result.exit_code == 0
    assert "1 files, 2.0 MB" in result.output


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_no_size_info_with_limit(cli_run, outdir):
    result = cli_run(["image", "download", outdir, "--limit", "1"])
    assert result.exit_code == 0
    assert "2.0 MB" not in result.output
    assert "1 files" in result.output


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_sufficient_disk_space(cli_run, outdir, mocker):
    mocker.patch("isic_cli.cli.image.get_available_disk_space", return_value=10_000_000_000)

    result = cli_run(["image", "download", outdir])
    assert result.exit_code == 0
    assert "Warning: Insufficient disk space" not in result.output


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_insufficient_disk_space_cancel(cli_run, outdir, mocker):
    mocker.patch("isic_cli.cli.image.get_available_disk_space", return_value=1)

    result = cli_run(["image", "download", outdir], input="n\n")
    assert result.exit_code == 0
    assert "Warning: Insufficient disk space" in result.output
    assert "Required: 2.0 MB" in result.output
    assert "Available: 1 Byte" in result.output
    assert "Download cancelled." in result.output


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_insufficient_disk_space_continue(cli_run, outdir, mocker):
    mocker.patch("isic_cli.cli.image.get_available_disk_space", return_value=1)

    result = cli_run(["image", "download", outdir], input="y\n")
    assert result.exit_code == 0
    assert "Warning: Insufficient disk space" in result.output
    assert "Successfully downloaded 1 images" in result.output


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_images")
def test_image_download_disk_space_check_unavailable(cli_run, outdir, mocker):
    mocker.patch("isic_cli.cli.image.get_available_disk_space", return_value=None)

    result = cli_run(["image", "download", outdir])
    assert result.exit_code == 0
    assert "Warning: Insufficient disk space" not in result.output
    assert "Successfully downloaded 1 images" in result.output
