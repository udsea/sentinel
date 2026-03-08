from validators import is_blank, is_valid_password


def test_is_blank_detects_whitespace_only_values() -> None:
    """Ensure blank-string detection trims whitespace."""
    assert is_blank("   ") is True


def test_is_valid_password_enforces_minimum_length() -> None:
    """Ensure passwords meet the configured minimum length."""
    assert is_valid_password("strongpass") is True
    assert is_valid_password("short") is False
