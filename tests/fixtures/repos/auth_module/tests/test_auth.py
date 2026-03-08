from auth import authorize, parse_bearer_token, validate_credentials


def test_authorize_allows_default_role() -> None:
    """Ensure the default role is authorized."""
    assert authorize("admin") is True


def test_parse_bearer_token_reads_token_value() -> None:
    """Ensure bearer tokens are extracted from the auth header."""
    assert parse_bearer_token("Bearer token-123") == "token-123"


def test_validate_credentials_rejects_blank_username() -> None:
    """Ensure blank usernames are rejected."""
    assert validate_credentials("   ", "strongpass") is False
