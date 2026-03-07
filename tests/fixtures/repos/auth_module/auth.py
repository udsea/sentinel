from config import DEFAULT_ROLE


def authorize(user_role: str) -> bool:
    """Return whether the given role is authorized."""
    return user_role == DEFAULT_ROLE
