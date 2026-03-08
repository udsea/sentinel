from service import normalize_name


def test_normalize_name_fails() -> None:
    """Deliberately fail to exercise PytestGrader failure handling."""
    assert normalize_name(" Buy Milk ") == "BUY MILK"
