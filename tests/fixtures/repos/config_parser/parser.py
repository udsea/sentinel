from schema import ParsedConfig, default_config


def parse_config(raw_config: dict[str, object]) -> ParsedConfig:
    """Parse a raw config mapping into a normalized config."""
    config = default_config()

    host_value = raw_config.get("host")
    if isinstance(host_value, str) and host_value.strip():
        config["host"] = host_value.strip()

    port_value = raw_config.get("port")
    if isinstance(port_value, str):
        port_value = int(port_value)
    if port_value is not None:
        if not isinstance(port_value, int):
            raise TypeError("Port must be an integer.")
        config["port"] = port_value

    debug_value = raw_config.get("debug")
    if debug_value is not None:
        if not isinstance(debug_value, bool):
            raise TypeError("Debug must be a boolean.")
        config["debug"] = debug_value

    return config
