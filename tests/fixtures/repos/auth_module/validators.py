from config import MIN_PASSWORD_LENGTH


def is_blank(value: str) -> bool:
    """Return whether a string is blank after trimming."""
    return not value.strip()


def is_valid_password(password: str) -> bool:
    """Validate password strength using a minimal length rule."""
    return len(password.strip()) >= MIN_PASSWORD_LENGTH
