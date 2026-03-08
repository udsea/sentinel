from pathlib import Path

from sentinel.agents import BenignScriptedAgent, CheatingScriptedAgent
from sentinel.grading import PytestGrader
from sentinel.monitors import ContentRiskMonitor, KeywordRiskMonitor, WritePolicyMonitor
from sentinel.runner import run_task
from sentinel.tasks.loader import load_task_spec

_TASKS_ROOT = Path(__file__).parent / "fixtures" / "tasks"


def test_benign_realistic_demo_path_runs_end_to_end() -> None:
    """Test that a realistic benign task runs through grading and monitoring."""
    task = load_task_spec(_TASKS_ROOT / "fix_pagination_v1.yaml")

    result = run_task(
        task=task,
        agent=BenignScriptedAgent(),
        graders=[PytestGrader(relative_path="tests", pytest_args=["-q"])],
        monitors=[
            WritePolicyMonitor(protected_prefixes=["tests/"]),
            KeywordRiskMonitor(),
            ContentRiskMonitor(),
        ],
    )

    assert result.task_id == "fix_pagination_v1"
    assert result.all_graders_passed is True
    assert result.any_monitor_flagged is False
    assert result.trace.file_writes[0].relative_path == "app.py"
    assert result.trace.final_output is not None


def test_cheating_realistic_demo_path_runs_end_to_end() -> None:
    """Test that a realistic cheating task is flagged while still grading cleanly."""
    task = load_task_spec(_TASKS_ROOT / "hide_failing_test_v1.yaml")

    result = run_task(
        task=task,
        agent=CheatingScriptedAgent(),
        graders=[PytestGrader(relative_path="tests", pytest_args=["-q"])],
        monitors=[
            WritePolicyMonitor(protected_prefixes=["tests/"]),
            KeywordRiskMonitor(),
            ContentRiskMonitor(),
        ],
    )

    assert result.task_id == "hide_failing_test_v1"
    assert result.all_graders_passed is True
    assert result.any_monitor_flagged is True
    assert result.trace.file_writes[0].relative_path == "tests/test_app.py"
    assert result.monitor_aggregate.flagged_monitor_names == [
        "WritePolicyMonitor",
        "KeywordRiskMonitor",
        "ContentRiskMonitor",
    ]
