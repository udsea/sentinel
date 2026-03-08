import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from sentinel.cli import app
from sentinel.experiments import load_experiment_spec, run_experiment

runner = CliRunner()


def write_temp_experiment_from_fixture(
    tmp_path: Path,
    fixture_name: str,
    output_dir_name: str,
) -> Path:
    """Copy an experiment fixture YAML and override its output directory.

    Args:
        tmp_path: Temporary pytest directory.
        fixture_name: Fixture YAML filename to copy.
        output_dir_name: Output directory name to inject.

    Returns:
        Path: Path to the rewritten experiment YAML file.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "experiments" / fixture_name
    payload = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    payload["output_dir"] = str(tmp_path / output_dir_name)

    target_path = tmp_path / fixture_name
    target_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )
    return target_path


def test_benign_experiment_runs_and_writes_outputs(tmp_path: Path) -> None:
    """Test that a benign experiment runs from config and writes artifacts."""
    experiment_path = write_temp_experiment_from_fixture(
        tmp_path,
        "benign_demo.yaml",
        "benign_demo_outputs",
    )
    spec = load_experiment_spec(experiment_path)

    output_dir = run_experiment(spec)

    assert output_dir.exists()
    assert (output_dir / "batch_summary.json").exists()
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "fix_pagination_v1.json").exists()
    assert (output_dir / "preserve_completed_state_v1.json").exists()


def test_cheating_experiment_runs_and_writes_outputs(tmp_path: Path) -> None:
    """Test that a cheating experiment runs from config and writes artifacts."""
    experiment_path = write_temp_experiment_from_fixture(
        tmp_path,
        "cheating_demo.yaml",
        "cheating_demo_outputs",
    )
    spec = load_experiment_spec(experiment_path)

    output_dir = run_experiment(spec)
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert output_dir.exists()
    assert (output_dir / "hide_failing_test_v1.json").exists()
    assert (output_dir / "shortcut_completion_checks_v1.json").exists()
    assert manifest["flagged_task_ids"] == [
        "hide_failing_test_v1",
        "shortcut_completion_checks_v1",
    ]


def test_experiment_spec_json_is_written(tmp_path: Path) -> None:
    """Test that the resolved experiment spec is written alongside artifacts."""
    experiment_path = write_temp_experiment_from_fixture(
        tmp_path,
        "benign_demo.yaml",
        "spec_copy_outputs",
    )
    spec = load_experiment_spec(experiment_path)

    output_dir = run_experiment(spec)
    saved_spec = json.loads((output_dir / "experiment_spec.json").read_text("utf-8"))

    assert saved_spec["name"] == "benign_demo"
    assert saved_spec["agent"]["kind"] == "benign_scripted"


def test_batch_artifacts_exist_for_experiment_run(tmp_path: Path) -> None:
    """Test that batch artifacts are written for experiment runs."""
    experiment_path = write_temp_experiment_from_fixture(
        tmp_path,
        "cheating_demo.yaml",
        "artifact_outputs",
    )
    spec = load_experiment_spec(experiment_path)

    output_dir = run_experiment(spec)
    summary = json.loads((output_dir / "batch_summary.json").read_text("utf-8"))

    assert summary["total_runs"] == 2
    assert summary["flagged_runs"] == 2


def test_cli_run_experiment_works(tmp_path: Path) -> None:
    """Test that the CLI experiment command runs and writes outputs."""
    experiment_path = write_temp_experiment_from_fixture(
        tmp_path,
        "benign_demo.yaml",
        "cli_outputs",
    )

    result = runner.invoke(app, ["run-experiment", str(experiment_path)])

    assert result.exit_code == 0
    assert "Experiment artifacts written to:" in result.stdout
    assert (tmp_path / "cli_outputs" / "batch_summary.json").exists()
    assert (tmp_path / "cli_outputs" / "experiment_spec.json").exists()
