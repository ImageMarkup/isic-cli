def test_base_command(cli_run):
    result = cli_run()

    assert result.exit_code == 0
    assert 'Usage: ' in result.output

    # The output of isic with no args and isic with --help should be identical
    help_result = cli_run(['--help'])
    assert help_result.exit_code == 0
    assert help_result.output == result.output
