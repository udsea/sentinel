from parser import parse_config


def test_parse_config_applies_default_port() -> None:
    """Ensure missing ports fall back to the default value."""
    assert parse_config({"host": "service.local"}) == {
        "host": "service.local",
        "port": 8080,
        "debug": False,
    }


def test_parse_config_accepts_string_port_values() -> None:
    """Ensure string port values are normalized to integers."""
    assert parse_config({"port": "9000", "debug": True}) == {
        "host": "localhost",
        "port": 9000,
        "debug": True,
    }
