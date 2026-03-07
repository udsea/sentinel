import json
from pathlib import Path
from typing import cast

from sentinel.runner import RunResult


def run_result_to_dict(result: RunResult) -> dict[str, object]:
    """Convert a run result into a JSON-safe dictionary.

    Args:
        result: Run result to serialize.

    Returns:
        dict[str, object]: JSON-safe dictionary representation.
    """
    payload = cast(dict[str, object], result.model_dump(mode="json"))
    payload["all_graders_passed"] = result.all_graders_passed
    payload["any_monitor_flagged"] = result.any_monitor_flagged
    return payload


def save_run_result_json(result: RunResult, path: str | Path) -> Path:
    """Serialize a run result and save it to a JSON file.

    Args:
        result: Run result to serialize.
        path: Output path for the JSON file.

    Returns:
        Path: Path to the written JSON file.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = run_result_to_dict(result)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path
