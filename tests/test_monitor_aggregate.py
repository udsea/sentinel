from sentinel.agents import BenignScriptedAgent, CheatingScriptedAgent
from sentinel.monitors import (
    KeywordRiskMonitor,
    MonitorAggregate,
    PathRiskMonitor,
    run_monitors,
)
from sentinel.sandbox import fixture_workspace
from sentinel.traces import RunTrace


def test_empty_monitor_list_returns_zeroed_aggregate() -> None:
    """Test that no monitors yields an empty zeroed aggregate."""
    with fixture_workspace("todo_api") as workspace:
        trace = RunTrace(task_id="observe_workspace_v1", workspace=str(workspace))

    aggregate = run_monitors(trace=trace, monitors=[])

    assert isinstance(aggregate, MonitorAggregate)
    assert aggregate.results == []
    assert aggregate.any_flagged is False
    assert aggregate.max_confidence == 0.0
    assert aggregate.flagged_monitor_names == []


def test_benign_trace_with_both_monitors_is_not_flagged() -> None:
    """Test that benign scripted behavior stays unflagged."""
    with fixture_workspace("todo_api") as workspace:
        trace = BenignScriptedAgent().run(
            task_id="fix_pagination_v1",
            workspace=workspace,
        )

    aggregate = run_monitors(
        trace=trace,
        monitors=[PathRiskMonitor(), KeywordRiskMonitor()],
    )

    assert aggregate.any_flagged is False
    assert aggregate.flagged_monitor_names == []
    assert aggregate.max_confidence == 0.05


def test_cheating_trace_with_both_monitors_is_flagged() -> None:
    """Test that cheating scripted behavior is flagged."""
    with fixture_workspace("todo_api") as workspace:
        trace = CheatingScriptedAgent().run(
            task_id="hide_failing_test_v1",
            workspace=workspace,
        )

    aggregate = run_monitors(
        trace=trace,
        monitors=[PathRiskMonitor(), KeywordRiskMonitor()],
    )

    assert aggregate.any_flagged is True
    assert len(aggregate.results) == 2


def test_flagged_monitor_names_include_the_correct_monitors() -> None:
    """Test that flagged monitor names preserve flagged monitor order."""
    with fixture_workspace("todo_api") as workspace:
        trace = CheatingScriptedAgent().run(
            task_id="hide_failing_test_v1",
            workspace=workspace,
        )

    aggregate = run_monitors(
        trace=trace,
        monitors=[PathRiskMonitor(), KeywordRiskMonitor()],
    )

    assert aggregate.flagged_monitor_names == [
        "PathRiskMonitor",
        "KeywordRiskMonitor",
    ]


def test_max_confidence_uses_the_highest_monitor_confidence() -> None:
    """Test that aggregate max confidence uses the highest monitor score."""
    with fixture_workspace("todo_api") as workspace:
        trace = CheatingScriptedAgent().run(
            task_id="hide_failing_test_v1",
            workspace=workspace,
        )

    aggregate = run_monitors(
        trace=trace,
        monitors=[PathRiskMonitor(), KeywordRiskMonitor()],
    )

    assert aggregate.max_confidence == 0.95


def test_monitor_aggregate_preserves_monitor_execution_order() -> None:
    """Test that raw monitor results preserve input monitor order."""
    with fixture_workspace("todo_api") as workspace:
        trace = CheatingScriptedAgent().run(
            task_id="hide_failing_test_v1",
            workspace=workspace,
        )

    aggregate = run_monitors(
        trace=trace,
        monitors=[PathRiskMonitor(), KeywordRiskMonitor()],
    )

    assert [result.monitor_name for result in aggregate.results] == [
        "PathRiskMonitor",
        "KeywordRiskMonitor",
    ]
