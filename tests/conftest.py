import functools

from click.testing import CliRunner
import pytest

from isic_cli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_run(runner):
    return functools.partial(runner.invoke, cli)


@pytest.fixture(autouse=True)
def mock_oauth(mocker):
    from girder_cli_oauth_client import GirderCliOAuthClient

    def maybe_restore_login(self):
        return {'Authorization': 'fake-credentials'}

    @property
    def auth_headers(self):
        return {'Authorization': 'fake-credentials'}

    mocker.patch.object(GirderCliOAuthClient, 'maybe_restore_login', maybe_restore_login)
    mocker.patch.object(GirderCliOAuthClient, 'auth_headers', auth_headers)
