from sentinel.schemas.task import TaskSpec
from sentinel.traces.events import validate_non_empty_text


def build_visible_task_prompt(task: TaskSpec) -> str:
    """Build the visible task prompt shared across Sentinel surfaces.

    Args:
        task: Task specification to render.

    Returns:
        str: Deterministic visible prompt text.
    """
    lines = [
        f"Goal: {task.goal}",
        "",
        "Instructions:",
        *[f"- {instruction}" for instruction in task.visible_instructions],
    ]
    return validate_non_empty_text("\n".join(lines))
