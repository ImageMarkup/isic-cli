from __future__ import annotations

from packaging.version import Version
import pytest

from isic_cli.utils.version import newest_version_available, upgrade_type


@pytest.fixture()
def _mock_pypi_files(mocker):
    mocker.patch(
        "isic_cli.utils.version._pypi_files",
        return_value=[
            {"filename": "isic_cli-0.0.1.tar.gz", "yanked": False},
            {"filename": "isic_cli-1.2.3-py3-none-any.whl"},
            {"filename": "isic_cli-1.2.3.tar.gz"},
            {"filename": "isic_cli-1.3.0-py3-none-any.whl", "yanked": True},
            {"filename": "isic_cli-1.4.0.tar.gz", "yanked": "Broken release"},
        ],
    )


@pytest.mark.usefixtures("_mock_pypi_files")
def test_newest_version_available():
    newest_version = newest_version_available()
    assert newest_version == Version("1.2.3"), newest_version


@pytest.mark.parametrize(
    ("from_version", "to_version", "expected"),
    [
        ("1.2.3", "2.0.0", "major"),
        ("1.2.3", "1.3.0", "minor"),
        ("1.2.3", "1.2.4", "micro"),
        ("1.2.3", "1.2.3", None),
        ("2.0.0", "1.5.0", None),
    ],
)
def test_upgrade_type(from_version, to_version, expected):
    assert upgrade_type(Version(from_version), Version(to_version)) == expected
