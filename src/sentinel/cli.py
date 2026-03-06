import typer

# Initialize the Typer app
app = typer.Typer(
    name="sentinel",
    help="Sentinel: Your security and monitoring assistant.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Display the current version of Sentinel."""
    typer.echo("sentinel version: dev")


@app.callback()
def main() -> None:
    """Sentinel CLI main entry point."""
    # This runs before any command (like global setup)
    pass


if __name__ == "__main__":
    app()
