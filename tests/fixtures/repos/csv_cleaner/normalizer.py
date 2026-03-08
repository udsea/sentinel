def normalize_header(header: str) -> str:
    """Normalize a CSV header to snake_case-ish text."""
    return header.strip().lower().replace(" ", "_")


def normalize_cell(value: str) -> str:
    """Trim surrounding whitespace from a CSV cell."""
    return value.strip()
