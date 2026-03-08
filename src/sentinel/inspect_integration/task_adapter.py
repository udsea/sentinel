from sentinel.inspect_integration.sample import InspectSample
from sentinel.schemas.task import TaskSpec
from sentinel.traces.events import validate_non_empty_text


def task_spec_to_inspect_sample(task: TaskSpec) -> InspectSample:
    """Convert a Sentinel task spec into an Inspect-aligned sample.

    Args:
        task: Task specification to convert.

    Returns:
        InspectSample: Inspect-facing sample payload.
    """
    metadata: dict[str, object] = {
        "track": task.track,
        "difficulty": task.difficulty,
        "goal": task.goal,
        "risk_tags": list(task.risk_tags),
        "hidden_constraints": list(task.hidden_constraints),
        "temptations": list(task.temptations),
        "expected_artifacts": list(task.expected_artifacts),
        "task_metadata": {key: value for key, value in task.metadata.items()},
    }

    return InspectSample(
        id=task.id,
        input=_build_task_prompt(task),
        metadata=metadata,
        sandbox_fixture=task.repo_fixture,
    )


def _build_task_prompt(task: TaskSpec) -> str:
    """Build a deterministic visible prompt from a task spec.

    Args:
        task: Task specification to render.

    Returns:
        str: Visible prompt text for an Inspect-facing sample.
    """
    lines = [
        f"Goal: {task.goal}",
        "",
        "Instructions:",
        *[f"- {instruction}" for instruction in task.visible_instructions],
    ]
    return validate_non_empty_text("\n".join(lines))
