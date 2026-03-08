from config import DEFAULT_ROLE, TOKEN_PREFIX
from validators import is_blank, is_valid_password


def authorize(user_role: str) -> bool:
    """Return whether the given role is authorized."""
    return user_role == DEFAULT_ROLE


def parse_bearer_token(header: str) -> str | None:
    """Parse a bearer token header."""
    if not header.startswith(TOKEN_PREFIX):
        return None

    token = header.removeprefix(TOKEN_PREFIX).strip()
    return token or None


def validate_credentials(username: str, password: str) -> bool:
    """Validate a username and password pair."""
    if is_blank(username):
        return False

    return is_valid_password(password)
