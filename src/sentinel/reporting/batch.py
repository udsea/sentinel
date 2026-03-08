import json
from collections.abc import Iterable, Sequence
from pathlib import Path

from sentinel.reporting.serialize import save_run_result_json
from sentinel.runner import RunResult, summarize_batch


def save_batch_results(
    results: Sequence[RunResult],
    output_dir: str | Path,
) -> Path:
    """Save a batch run artifact bundle to disk.

    Args:
        results: Run results to persist.
        output_dir: Directory where the batch bundle should be written.

    Returns:
        Path: The created output directory.
    """
    bundle_dir = Path(output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    _remove_stale_run_json_files(bundle_dir, results)

    for result in results:
        save_run_result_json(result, bundle_dir / f"{result.task_id}.json")

    _write_json_file(bundle_dir / "batch_summary.json", summarize_batch(results))
    _write_json_file(bundle_dir / "manifest.json", build_batch_manifest(results))
    return bundle_dir


def build_batch_manifest(results: Sequence[RunResult]) -> dict[str, object]:
    """Build a compact manifest for a batch run.

    Args:
        results: Run results to summarize in the manifest.

    Returns:
        dict[str, object]: JSON-safe manifest payload.
    """
    task_ids = [result.task_id for result in results]
    flagged_task_ids = [
        result.task_id for result in results if result.any_monitor_flagged
    ]
    passed_task_ids = [
        result.task_id for result in results if result.all_graders_passed
    ]
    agent_names = _stable_unique(result.agent_name for result in results)

    return {
        "total_runs": len(results),
        "task_ids": task_ids,
        "agent_names": agent_names,
        "flagged_task_ids": flagged_task_ids,
        "passed_task_ids": passed_task_ids,
    }


def _stable_unique(values: Iterable[str]) -> list[str]:
    """Return stable-order unique strings.

    Args:
        values: Input strings in encounter order.

    Returns:
        list[str]: Stable-order unique values.
    """
    seen: set[str] = set()
    unique_values: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)

    return unique_values


def _write_json_file(path: Path, payload: dict[str, object]) -> Path:
    """Write a JSON payload to disk.

    Args:
        path: Output path to write.
        payload: JSON-safe payload to serialize.

    Returns:
        Path: The written path.
    """
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _remove_stale_run_json_files(
    bundle_dir: Path,
    results: Sequence[RunResult],
) -> None:
    """Remove stale per-run JSON files from a reused batch artifact directory.

    Args:
        bundle_dir: Existing batch artifact directory.
        results: Current run results that should remain in the bundle.
    """
    keep_names = {
        "batch_summary.json",
        "manifest.json",
        "experiment_spec.json",
        *[f"{result.task_id}.json" for result in results],
    }

    for path in bundle_dir.glob("*.json"):
        if path.name not in keep_names:
            path.unlink()
