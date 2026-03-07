from auth import authorize


def test_authorize_allows_default_role() -> None:
    """Ensure the default role is authorized."""
    assert authorize("admin") is True
