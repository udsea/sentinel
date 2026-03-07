from app import create_item


def test_create_item_normalizes_names() -> None:
    """Ensure todo items are normalized."""
    assert create_item(" Buy Milk ") == {"name": "buy milk"}
