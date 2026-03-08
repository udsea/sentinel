from normalizer import normalize_cell, normalize_header


def clean_headers(headers: list[str]) -> list[str]:
    """Normalize a sequence of CSV headers."""
    return [normalize_header(header) for header in headers]


def clean_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Normalize rows and drop entries that are fully empty."""
    cleaned_rows: list[dict[str, str]] = []

    for row in rows:
        normalized_row = {
            normalize_header(key): normalize_cell(value) for key, value in row.items()
        }
        if any(value for value in normalized_row.values()):
            cleaned_rows.append(normalized_row)

    return cleaned_rows
