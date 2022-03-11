from packaging.version import Version
import pytest


def test_base_command(cli_run):
    result = cli_run()

    assert result.exit_code == 0
    assert 'Usage: ' in result.output

    # The output of isic with no args and isic with --help should be identical
    help_result = cli_run(['--help'])
    assert help_result.exit_code == 0
    assert help_result.output == result.output


@pytest.mark.parametrize(
    'current_version,latest_version,expected_exit_code,output_pattern',
    [
        [Version('0.0.1'), Version('0.1.0'), 0, 'new version'],
        [Version('0.0.1'), Version('1.0.0'), 1, 'new major version'],
    ],
)
def test_new_version(
    cli_run, mocker, current_version, latest_version, expected_exit_code, output_pattern
):
    mocker.patch('isic_cli.utils.version.get_version', return_value=current_version)
    mocker.patch('isic_cli.utils.version.newest_version_available', return_value=latest_version)

    # The command is arbitrary, it just normally exits 0 with no mocking necessary
    result = cli_run(['user', 'print-token'])

    assert result.exit_code == expected_exit_code
    assert output_pattern in result.output
