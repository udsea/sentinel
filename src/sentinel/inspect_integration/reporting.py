import json
from pathlib import Path

from sentinel.inspect_integration.executor import InspectExecutionResult
from sentinel.reporting.serialize import run_result_to_dict, save_run_result_json


def inspect_execution_to_dict(
    execution: InspectExecutionResult,
) -> dict[str, object]:
    """Convert an Inspect execution result into a JSON-safe dictionary.

    Args:
        execution: Inspect execution result to serialize.

    Returns:
        dict[str, object]: JSON-safe execution payload.
    """
    return {
        "task_name": execution.task_name,
        "batch_summary": dict(execution.batch_summary),
        "results": [run_result_to_dict(result) for result in execution.results],
        "task_ids": [result.task_id for result in execution.results],
    }


def save_inspect_execution(
    execution: InspectExecutionResult,
    output_dir: str | Path,
) -> Path:
    """Write Inspect execution artifacts to disk.

    Args:
        execution: Inspect execution result to persist.
        output_dir: Directory where artifacts should be written.

    Returns:
        Path: Created output directory.
    """
    bundle_dir = Path(output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for result in execution.results:
        save_run_result_json(result, bundle_dir / f"{result.task_id}.json")

    _write_json_file(
        bundle_dir / "inspect_execution.json",
        inspect_execution_to_dict(execution),
    )
    _write_json_file(bundle_dir / "batch_summary.json", dict(execution.batch_summary))
    return bundle_dir


def summarize_inspect_execution(
    execution: InspectExecutionResult,
) -> str:
    """Return a short human-readable summary for an Inspect execution.

    Args:
        execution: Inspect execution result to summarize.

    Returns:
        str: Multi-line summary text.
    """
    batch_summary = execution.batch_summary
    task_ids = ", ".join(result.task_id for result in execution.results) or "<none>"

    lines = [
        f"Inspect task: {execution.task_name}",
        f"Total runs: {batch_summary.get('total_runs', 0)}",
        f"Passed runs: {batch_summary.get('passed_runs', 0)}",
        f"Flagged runs: {batch_summary.get('flagged_runs', 0)}",
        f"Task ids: {task_ids}",
    ]
    return "\n".join(lines)


def _write_json_file(path: Path, payload: dict[str, object]) -> Path:
    """Write a JSON payload to disk.

    Args:
        path: Output path to write.
        payload: JSON-safe payload to serialize.

    Returns:
        Path: Written path.
    """
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
