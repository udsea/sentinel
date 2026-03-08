from models import TodoItem
from service import create_todo_item, paginate_items


def test_create_todo_item_preserves_completed_flag() -> None:
    """Ensure todo items preserve the completed flag."""
    assert create_todo_item(" Ship Patch ", completed=True) == {
        "id": 1,
        "name": "ship patch",
        "completed": True,
    }


def test_paginate_items_clamps_invalid_page_numbers() -> None:
    """Ensure invalid page values fall back to the first page."""
    items: list[TodoItem] = [
        {"id": 1, "name": "buy milk", "completed": False},
        {"id": 2, "name": "ship patch", "completed": True},
        {"id": 3, "name": "review pr", "completed": False},
    ]

    assert paginate_items(items, page=0, page_size=2) == items[:2]
