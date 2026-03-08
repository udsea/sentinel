from pathlib import Path

import yaml
from pydantic import ValidationError

from sentinel.experiments.schema import ExperimentSpec


class ExperimentSpecLoadError(ValueError):
    """Raised when an experiment spec cannot be parsed or validated."""


def load_experiment_spec(path: str | Path) -> ExperimentSpec:
    """Load and validate an experiment spec from YAML.

    Args:
        path: Path to the YAML experiment specification file.

    Returns:
        ExperimentSpec: Validated experiment specification.

    Raises:
        FileNotFoundError: If the file does not exist.
        ExperimentSpecLoadError: If the YAML is malformed or invalid.
    """
    file_path = Path(path)
    raw_text = file_path.read_text(encoding="utf-8")

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as error:
        raise ExperimentSpecLoadError(
            f"Malformed YAML in experiment spec file '{file_path}': {error}"
        ) from error

    if data is None:
        raise ExperimentSpecLoadError(f"Experiment spec file '{file_path}' is empty.")

    if not isinstance(data, dict):
        raise ExperimentSpecLoadError(
            f"Experiment spec file '{file_path}' must contain a top-level mapping."
        )

    try:
        return ExperimentSpec.model_validate(data)
    except ValidationError as error:
        raise ExperimentSpecLoadError(
            f"Experiment spec validation failed for '{file_path}': {error}"
        ) from error
