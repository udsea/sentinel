from typer.testing import CliRunner

from sentinel.cli import app

runner = CliRunner()


def test_version_command():
    """Test that the version command returns the correct string.

    Args:
        None

    Returns:
        None
    """
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "sentinel version: dev" in result.stdout


def test_help_flag():
    """Test that the --help flag displays the help menu.

    Args:
        None

    Returns:
        None
    """
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Show this message and exit" in result.stdout
    assert "version" in result.stdout
