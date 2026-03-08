from typing import TypedDict


class TodoItem(TypedDict):
    """Typed representation of a todo item."""

    id: int
    name: str
    completed: bool


def make_item(item_id: int, name: str, completed: bool = False) -> TodoItem:
    """Create a todo item record."""
    return {"id": item_id, "name": name, "completed": completed}
