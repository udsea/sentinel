from pathlib import Path

import yaml
from pydantic import ValidationError

from sentinel.schemas.task import TaskSpec


class TaskSpecLoadError(ValueError):
    """Raised when a task spec cannot be loaded or validated."""


def load_task_spec(path: str | Path) -> TaskSpec:
    """Load and validate a TaskSpec from a YAML file.

    Args:
        path: Path to the YAML task specification file.

    Returns:
        TaskSpec: The validated task specification.

    Raises:
        TaskSpecLoadError: If the YAML is malformed, the top-level structure is
            not a mapping, or schema validation fails.
    """
    file_path = Path(path)

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TaskSpecLoadError(
            f"Failed to read task spec file '{file_path}': {exc}"
        ) from exc

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise TaskSpecLoadError(
            f"Malformed YAML in task spec file '{file_path}': {exc}"
        ) from exc

    if data is None:
        raise TaskSpecLoadError(f"Task spec file '{file_path}' is empty.")

    if not isinstance(data, dict):
        raise TaskSpecLoadError(
            f"Task spec file '{file_path}' must contain a top-level mapping."
        )

    try:
        return TaskSpec.model_validate(data)
    except ValidationError as exc:
        raise TaskSpecLoadError(
            f"Task spec validation failed for '{file_path}': {exc}"
        ) from exc
