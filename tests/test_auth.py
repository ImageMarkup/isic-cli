def test_auth_login_logged_in(cli_run, mock_user):
    result = cli_run(['auth', 'login'])
    assert result.exit_code == 0
    assert 'Hello' in result.output
