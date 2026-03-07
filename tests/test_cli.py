from typer.testing import CliRunner

from sentinel import __version__
from sentinel.cli import app

runner = CliRunner()


def test_no_args_runs_version() -> None:
    """Test that invoking the CLI with no arguments runs the version command.

    Because the application currently exposes a single command, Typer treats
    it as the root command. Invoking the CLI with no arguments should execute
    the command and print the current Sentinel version.
    """
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert f"sentinel version: {__version__}" in result.stdout


def test_help_flag_displays_help() -> None:
    """Test that the help flag displays CLI help output.

    The help output should render successfully and include at least the
    application name.
    """
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "sentinel" in result.stdout.lower()


def test_explicit_version_subcommand_fails_for_single_command_app() -> None:
    """Test that using 'version' as a subcommand fails in single-command mode.

    When a Typer application defines only one command, Typer exposes it as the
    root command rather than as a named subcommand. Passing 'version'
    explicitly should therefore return a usage error.
    """
    result = runner.invoke(app, ["version"])

    assert result.exit_code != 0
