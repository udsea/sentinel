from normalizer import normalize_cell, normalize_header


def test_normalize_header_trims_and_snake_cases_text() -> None:
    """Ensure headers are lowercased and space-normalized."""
    assert normalize_header(" Display Name ") == "display_name"


def test_normalize_cell_trims_surrounding_whitespace() -> None:
    """Ensure cell values are trimmed."""
    assert normalize_cell("  alice@example.com  ") == "alice@example.com"
