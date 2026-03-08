from pathlib import Path

import pytest
import yaml

from sentinel.experiments import (
    ExperimentSpec,
    ExperimentSpecLoadError,
    load_experiment_spec,
)


def write_experiment_yaml(
    tmp_path: Path,
    filename: str,
    payload: dict[str, object],
) -> Path:
    """Write an experiment YAML fixture for schema tests.

    Args:
        tmp_path: Temporary pytest directory.
        filename: YAML filename to create.
        payload: Experiment payload to dump.

    Returns:
        Path: Path to the created YAML file.
    """
    path = tmp_path / filename
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def make_valid_payload() -> dict[str, object]:
    """Create a valid experiment payload for schema tests.

    Returns:
        dict[str, object]: Valid experiment payload.
    """
    return {
        "name": "demo_experiment",
        "tasks": ["tests/fixtures/tasks/fix_pagination_v1.yaml"],
        "agent": {"kind": "benign_scripted"},
        "graders": [{"kind": "pytest", "relative_path": ".", "pytest_args": ["-q"]}],
        "monitors": [{"kind": "path_risk"}],
        "output_dir": "outputs/demo_experiment",
    }


def test_valid_experiment_yaml_loads() -> None:
    """Test that a valid experiment fixture YAML loads successfully."""
    fixture_path = (
        Path(__file__).parent / "fixtures" / "experiments" / "benign_demo.yaml"
    )

    spec = load_experiment_spec(fixture_path)

    assert isinstance(spec, ExperimentSpec)
    assert spec.name == "benign_demo"
    assert len(spec.tasks) == 2


def test_invalid_agent_kind_fails(tmp_path: Path) -> None:
    """Test that invalid agent kinds fail validation."""
    payload = make_valid_payload()
    payload["agent"] = {"kind": "mystery_agent"}
    path = write_experiment_yaml(tmp_path, "invalid_agent.yaml", payload)

    with pytest.raises(ExperimentSpecLoadError, match="validation failed"):
        load_experiment_spec(path)


def test_invalid_grader_kind_fails(tmp_path: Path) -> None:
    """Test that invalid grader kinds fail validation."""
    payload = make_valid_payload()
    payload["graders"] = [{"kind": "mystery_grader"}]
    path = write_experiment_yaml(tmp_path, "invalid_grader.yaml", payload)

    with pytest.raises(ExperimentSpecLoadError, match="validation failed"):
        load_experiment_spec(path)


def test_invalid_monitor_kind_fails(tmp_path: Path) -> None:
    """Test that invalid monitor kinds fail validation."""
    payload = make_valid_payload()
    payload["monitors"] = [{"kind": "mystery_monitor"}]
    path = write_experiment_yaml(tmp_path, "invalid_monitor.yaml", payload)

    with pytest.raises(ExperimentSpecLoadError, match="validation failed"):
        load_experiment_spec(path)


def test_missing_tasks_fails(tmp_path: Path) -> None:
    """Test that missing task lists fail validation."""
    payload = make_valid_payload()
    del payload["tasks"]
    path = write_experiment_yaml(tmp_path, "missing_tasks.yaml", payload)

    with pytest.raises(ExperimentSpecLoadError, match="validation failed"):
        load_experiment_spec(path)


def test_empty_task_list_fails(tmp_path: Path) -> None:
    """Test that empty task lists fail validation."""
    payload = make_valid_payload()
    payload["tasks"] = []
    path = write_experiment_yaml(tmp_path, "empty_tasks.yaml", payload)

    with pytest.raises(ExperimentSpecLoadError, match="validation failed"):
        load_experiment_spec(path)
