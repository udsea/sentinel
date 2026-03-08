from typer.testing import CliRunner

from sentinel import __version__
from sentinel.cli import app

runner = CliRunner()


def test_version_command() -> None:
    """Test that the version subcommand prints the current package version.

    Args:
        None.

    Returns:
        None.
    """
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert f"sentinel version: {__version__}" in result.stdout


def test_help_flag_displays_help() -> None:
    """Test that the help flag displays the CLI help output.

    Args:
        None.

    Returns:
        None.
    """
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "sentinel" in result.stdout.lower()
    assert "version" in result.stdout.lower()
