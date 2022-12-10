def test_user_login_logged_in(cli_run, mock_user):
    result = cli_run(["user", "login"])
    assert result.exit_code == 0
    assert "Hello" in result.output
