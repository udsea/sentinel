from app import create_item, list_items


def test_create_item_normalizes_names() -> None:
    """Ensure todo items are normalized."""
    assert create_item(" Buy Milk ") == {"name": "buy milk"}


def test_list_items_returns_requested_page() -> None:
    """Ensure list pagination returns the requested slice."""
    assert list_items(page=2, page_size=2) == [
        {"id": 3, "name": "review pr", "completed": False}
    ]
