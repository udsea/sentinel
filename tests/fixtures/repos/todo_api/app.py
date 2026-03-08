from models import TodoItem
from service import create_todo_item, paginate_items

_SAMPLE_ITEMS: list[TodoItem] = [
    {"id": 1, "name": "buy milk", "completed": False},
    {"id": 2, "name": "ship patch", "completed": True},
    {"id": 3, "name": "review pr", "completed": False},
]


def create_item(name: str) -> dict[str, str]:
    """Create a normalized todo item response."""
    created_item = create_todo_item(name)
    return {"name": created_item["name"]}


def list_items(page: int = 1, page_size: int = 2) -> list[TodoItem]:
    """Return a paginated list of todo items."""
    return paginate_items(_SAMPLE_ITEMS, page=page, page_size=page_size)
