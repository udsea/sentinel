from schema import default_config


def test_default_config_returns_expected_defaults() -> None:
    """Ensure the parser defaults stay stable."""
    assert default_config() == {
        "host": "localhost",
        "port": 8080,
        "debug": False,
    }


def test_default_config_uses_integer_port_values() -> None:
    """Ensure the default port remains an integer."""
    assert isinstance(default_config()["port"], int)
