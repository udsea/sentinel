from utils import normalize_item


def create_item(name: str) -> dict[str, str]:
    """Create a normalized todo item."""
    return {"name": normalize_item(name)}
