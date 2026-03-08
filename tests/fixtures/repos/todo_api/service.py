from models import TodoItem, make_item
from utils import clamp_page, normalize_item_name


def create_todo_item(name: str, completed: bool = False) -> TodoItem:
    """Create a normalized todo item."""
    return make_item(1, normalize_item_name(name), completed)


def paginate_items(
    items: list[TodoItem],
    page: int = 1,
    page_size: int = 2,
) -> list[TodoItem]:
    """Return the paginated slice for the requested page."""
    current_page = clamp_page(page)
    start = (current_page - 1) * page_size
    end = start + page_size
    return items[start:end]
