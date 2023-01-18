import functools

from click.testing import CliRunner
import pytest

from isic_cli.cli import cli


@pytest.fixture(autouse=True)
def mock_sentry_setup(mocker):
    mocker.patch("isic_cli.cli._sentry_setup", return_value=None)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_run(runner):
    return functools.partial(runner.invoke, cli)


@pytest.fixture
def isolated_filesystem(runner):
    with runner.isolated_filesystem():
        yield


@pytest.fixture()
def mock_user(mocker):
    from girder_cli_oauth_client import GirderCliOAuthClient

    def maybe_restore_login(self):
        return {"Authorization": "fake-credentials"}

    @property
    def auth_headers(self):
        return {"Authorization": "fake-credentials"}

    mocker.patch.object(GirderCliOAuthClient, "maybe_restore_login", maybe_restore_login)
    mocker.patch.object(GirderCliOAuthClient, "auth_headers", auth_headers)

    mocker.patch("isic_cli.cli.get_users_me", return_value={"email": "fakeuser@email.test"})
