from packaging.version import Version
import pytest

from isic_cli.utils.version import newest_version_available


@pytest.fixture
def mock_pypi_releases(mocker):
    mocker.patch(
        "isic_cli.utils.version._pypi_releases", return_value={"0.0.1": None, "1.2.3": None}
    )


def test_newest_version_available(mock_pypi_releases):
    newest_version = newest_version_available()
    assert newest_version == Version("1.2.3"), newest_version
