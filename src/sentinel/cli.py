import typer

from sentinel import __version__

# Initialize the Typer app
app = typer.Typer(
    name="sentinel",
    help="Inspect-based evaluation framework for coding agents.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Display the current version of Sentinel."""
    typer.echo(f"sentinel version: {__version__}")


if __name__ == "__main__":
    app()
