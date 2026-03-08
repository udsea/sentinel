from typing import TypedDict


class ParsedConfig(TypedDict):
    """Typed representation of a parsed config."""

    host: str
    port: int
    debug: bool


def default_config() -> ParsedConfig:
    """Return the default config used by the parser."""
    return {"host": "localhost", "port": 8080, "debug": False}
