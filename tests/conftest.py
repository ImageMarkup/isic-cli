from __future__ import annotations

import functools

from click.testing import CliRunner
import pytest

from isic_cli.cli import cli


@pytest.fixture(autouse=True)
def _mock_sentry_setup(mocker):
    mocker.patch("isic_cli.cli._sentry_setup", return_value=None)


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def runner_non_utf8():
    return CliRunner(charset="cp1251")


@pytest.fixture()
def cli_run(runner):
    return functools.partial(runner.invoke, cli)


@pytest.fixture()
def cli_run_non_utf8(runner_non_utf8):
    return functools.partial(runner_non_utf8.invoke, cli)


@pytest.fixture()
def _isolated_filesystem(runner):
    with runner.isolated_filesystem():
        yield


@pytest.fixture()
def _mock_user(mocker):
    from girder_cli_oauth_client import GirderCliOAuthClient

    def maybe_restore_login(self):
        return {"Authorization": "fake-credentials"}

    @property
    def auth_headers(self):
        return {"Authorization": "fake-credentials"}

    mocker.patch.object(GirderCliOAuthClient, "maybe_restore_login", maybe_restore_login)
    mocker.patch.object(GirderCliOAuthClient, "auth_headers", auth_headers)

    mocker.patch("isic_cli.cli.get_users_me", return_value={"email": "fakeuser@email.test"})
