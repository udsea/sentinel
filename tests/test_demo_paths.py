import json
from pathlib import Path
from typing import Any, cast

from sentinel.agents import BenignScriptedAgent, CheatingScriptedAgent
from sentinel.grading import PytestGrader
from sentinel.monitors import (
    ContentRiskMonitor,
    KeywordRiskMonitor,
    PathRiskMonitor,
    WritePolicyMonitor,
)
from sentinel.monitors.base import BaseMonitor
from sentinel.reporting import save_run_result_json
from sentinel.runner import run_task
from sentinel.tasks.loader import load_task_spec

_TASKS_ROOT = Path(__file__).parent / "fixtures" / "tasks"


def test_benign_realistic_demo_path_runs_end_to_end(tmp_path: Path) -> None:
    """Test the canonical benign demo path end to end."""
    task = load_task_spec(_TASKS_ROOT / "fix_pagination_v1.yaml")

    result = run_task(
        task=task,
        agent=BenignScriptedAgent(),
        graders=[PytestGrader(relative_path="tests", pytest_args=["-q"])],
        monitors=_demo_monitors(),
    )
    output_path = save_run_result_json(result, tmp_path / "benign_run.json")
    payload = cast(dict[str, Any], json.loads(output_path.read_text(encoding="utf-8")))

    assert result.task_id == "fix_pagination_v1"
    assert result.all_graders_passed is True
    assert result.any_monitor_flagged is False
    assert result.trace.file_writes[0].relative_path == "app.py"
    assert result.trace.final_output is not None
    assert output_path.exists()
    assert payload["all_graders_passed"] is True
    assert payload["any_monitor_flagged"] is False
    assert payload["monitor_aggregate"]["flagged_monitor_names"] == []


def test_cheating_realistic_demo_path_runs_end_to_end(tmp_path: Path) -> None:
    """Test the canonical cheating demo path end to end."""
    task = load_task_spec(_TASKS_ROOT / "hide_failing_test_v1.yaml")

    result = run_task(
        task=task,
        agent=CheatingScriptedAgent(),
        graders=[PytestGrader(relative_path="tests", pytest_args=["-q"])],
        monitors=_demo_monitors(),
    )
    output_path = save_run_result_json(result, tmp_path / "cheating_run.json")
    payload = cast(dict[str, Any], json.loads(output_path.read_text(encoding="utf-8")))

    assert result.task_id == "hide_failing_test_v1"
    assert result.all_graders_passed is True
    assert result.any_monitor_flagged is True
    assert result.trace.file_writes[0].relative_path == "tests/test_app.py"
    assert result.monitor_aggregate.flagged_monitor_names == [
        "PathRiskMonitor",
        "KeywordRiskMonitor",
        "ContentRiskMonitor",
        "WritePolicyMonitor",
    ]
    assert output_path.exists()
    assert payload["all_graders_passed"] is True
    assert payload["any_monitor_flagged"] is True
    assert payload["monitor_aggregate"]["flagged_monitor_names"] == [
        "PathRiskMonitor",
        "KeywordRiskMonitor",
        "ContentRiskMonitor",
        "WritePolicyMonitor",
    ]


def _demo_monitors() -> list[BaseMonitor]:
    """Return the canonical monitor set for the public demo path."""
    return [
        PathRiskMonitor(),
        KeywordRiskMonitor(),
        ContentRiskMonitor(),
        WritePolicyMonitor(protected_prefixes=["tests/"]),
    ]
