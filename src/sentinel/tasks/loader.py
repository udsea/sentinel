from pathlib import Path

import yaml
from pydantic import ValidationError

from sentinel.schemas.task import TaskSpec


class TaskSpecLoadError(ValueError):
    """Raised when a task spec cannot be parsed or validated."""


def load_task_spec(path: str | Path) -> TaskSpec:
    """Load and validate a TaskSpec from a YAML file.

    Args:
        path: Path to the YAML task specification file.

    Returns:
        TaskSpec: A validated task specification.

    Raises:
        FileNotFoundError: If the file does not exist.
        TaskSpecLoadError: If the YAML is malformed, the top-level value is not
            a mapping, or schema validation fails.
    """
    file_path = Path(path)

    raw_text = file_path.read_text(encoding="utf-8")

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


def load_task_specs(paths: list[str | Path]) -> list[TaskSpec]:
    """Load and validate multiple TaskSpec files.

    Args:
        paths: A list of YAML task specification file paths.

    Returns:
        list[TaskSpec]: A list of validated task specifications.

    Raises:
        FileNotFoundError: If any file does not exist.
        TaskSpecLoadError: If any YAML file is malformed or fails schema
            validation.
    """
    return [load_task_spec(path) for path in paths]
