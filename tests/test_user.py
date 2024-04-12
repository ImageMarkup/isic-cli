from __future__ import annotations

import pytest


@pytest.mark.usefixtures("_isolated_filesystem", "_mock_user")
def test_user_login_logged_in(cli_run):
    result = cli_run(["user", "login"])
    assert result.exit_code == 0
    assert "Hello" in result.output
