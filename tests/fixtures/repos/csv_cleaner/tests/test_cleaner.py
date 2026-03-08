from cleaner import clean_headers, clean_rows


def test_clean_headers_normalizes_header_names() -> None:
    """Ensure CSV headers are normalized."""
    assert clean_headers([" First Name ", "Team Name"]) == [
        "first_name",
        "team_name",
    ]


def test_clean_rows_drops_fully_empty_rows() -> None:
    """Ensure empty rows are removed after normalization."""
    assert clean_rows(
        [
            {" Name ": " Alice ", "Team": " Ops "},
            {" Name ": "   ", "Team": "   "},
        ]
    ) == [{"name": "Alice", "team": "Ops"}]
