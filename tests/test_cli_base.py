from __future__ import annotations

import sys

from packaging.version import Version
import pytest


def test_base_command(cli_run):
    result = cli_run()

    assert result.exit_code == 2
    assert "Usage: " in result.output

    # The output of isic with no args and isic with --help should be identical
    help_result = cli_run(["--help"])
    assert help_result.exit_code == 0
    assert help_result.output == result.output


@pytest.mark.parametrize(
    ("current_version", "latest_version", "expected_exit_code", "output_pattern"),
    [
        (Version("0.0.1"), Version("0.1.0"), 0, "new version"),
        (Version("0.0.1"), Version("1.0.0"), 1, "new major version"),
    ],
)
def test_new_version(
    cli_run, mocker, current_version, latest_version, expected_exit_code, output_pattern
):
    mocker.patch("isic_cli.utils.version.get_version", return_value=current_version)
    mocker.patch("isic_cli.utils.version.newest_version_available", return_value=latest_version)

    # The command is arbitrary, it just normally exits 0 with no mocking necessary
    result = cli_run(["user", "print-token"], catch_exceptions=False)

    assert result.exit_code == expected_exit_code
    assert output_pattern in result.output


@pytest.mark.parametrize(
    ("interactive", "sentry_initialized", "send_bug_report", "capture_exception_sent"),
    [
        (True, True, "y", 1),
        (True, True, "n", 0),
        (False, True, None, 0),
        (True, False, None, 0),
    ],
)
def test_sentry_error_capture(
    mocker, capsys, interactive, sentry_initialized, send_bug_report, capture_exception_sent
):
    # Note: _sentry_setup is always mocked
    from isic_cli import cli
    from isic_cli.cli import main

    mocker.patch("isic_cli.cli.collection.get_collections", side_effect=RuntimeError("foo"))
    mocker.patch.object(
        sys, "argv", ["isic", "--guest", "--no-version-check", "collection", "list"]
    )
    prompt = mocker.patch("isic_cli.cli.click.prompt", return_value=send_bug_report)
    mocker.patch("isic_cli.cli.is_dev_install", return_value=False)
    stdin = mocker.patch.object(sys, "stdin")
    stdin.isatty.return_value = interactive
    mocker.patch("isic_cli.cli.sentry_sdk.is_initialized", return_value=sentry_initialized)

    spy = mocker.spy(cli, "capture_exception")
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert prompt.called == (interactive and sentry_initialized)
    assert spy.call_count == capture_exception_sent
    issue_link_shown = (
        "https://github.com/ImageMarkup/isic-cli/issues/new" in capsys.readouterr().err
    )
    assert issue_link_shown == (capture_exception_sent == 0)


@pytest.mark.usefixtures("_mock_user")
def test_bug_report_describes_env_and_user(mocker, capsys):
    from isic_cli.cli import main

    user = {"id": 1, "email": "fakeuser@email.test"}
    mocker.patch("isic_cli.cli.get_users_me", return_value=user)
    mocker.patch("isic_cli.cli.collection.get_collections", side_effect=RuntimeError("foo"))
    mocker.patch("isic_cli.cli.is_dev_install", return_value=True)
    mocker.patch.object(
        sys, "argv", ["isic", "--sandbox", "--no-version-check", "collection", "list"]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "RuntimeError: foo" in err
    assert "env:      sandbox" in err
    assert f"user:     {user['id']}" in err


def test_connection_error_is_not_reported_as_bug(mocker, capsys):
    from requests.exceptions import SSLError

    from isic_cli import cli
    from isic_cli.cli import main

    mocker.patch(
        "isic_cli.cli.collection.get_collections",
        side_effect=SSLError("EOF occurred in violation of protocol"),
    )
    mocker.patch.object(
        sys, "argv", ["isic", "--guest", "--no-version-check", "collection", "list"]
    )
    mocker.patch("isic_cli.cli.is_dev_install", return_value=False)
    prompt = mocker.patch("isic_cli.cli.click.prompt")
    spy = mocker.spy(cli, "capture_exception")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "Unable to connect to the ISIC Archive" in capsys.readouterr().err
    prompt.assert_not_called()
    assert spy.call_count == 0


@pytest.mark.parametrize("command", ["image", "metadata"])
def test_download_help(cli_run, command):
    result = cli_run([command, "download", "--help"])

    assert result.exit_code == 0, result.exception
    assert "The search query uses a simple DSL syntax." in result.output
