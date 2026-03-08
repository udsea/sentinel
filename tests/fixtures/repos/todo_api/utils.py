def normalize_item_name(name: str) -> str:
    """Normalize an item name for storage."""
    return " ".join(name.strip().lower().split())


def clamp_page(page: int) -> int:
    """Clamp pagination input to a valid one-based page number."""
    return page if page > 0 else 1
