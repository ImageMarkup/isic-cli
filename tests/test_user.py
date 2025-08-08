from __future__ import annotations

from authlib.integrations.base_client.errors import OAuthError
from girder_cli_oauth_client import GirderCliOAuthClient
import pytest


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_user")
def test_user_login_logged_in(cli_run):
    result = cli_run(["user", "login"])
    assert result.exit_code == 0
    assert "Hello" in result.output


@pytest.mark.usefixtures("_isolated_filesystem")
def test_user_login_oauth_timeout(cli_run, mocker):
    mock_login = mocker.patch.object(
        GirderCliOAuthClient, "login", side_effect=OAuthError(error="invalid_grant")
    )

    result = cli_run(["user", "login"])
    assert result.exit_code == 1
    assert "Logging in timed out or had an unexpected error" in result.output
    mock_login.assert_called_once()
