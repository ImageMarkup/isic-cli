from __future__ import annotations

from packaging.version import Version
import pytest

from isic_cli.utils.version import newest_version_available


@pytest.fixture()
def _mock_pypi_releases(mocker):
    mocker.patch(
        "isic_cli.utils.version._pypi_releases", return_value={"0.0.1": None, "1.2.3": None}
    )


@pytest.mark.usefixtures("_mock_pypi_releases")
def test_newest_version_available():
    newest_version = newest_version_available()
    assert newest_version == Version("1.2.3"), newest_version
