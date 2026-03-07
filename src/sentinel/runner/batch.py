from collections.abc import Sequence

from sentinel.agents.base import BaseAgent
from sentinel.grading.base import BaseGrader
from sentinel.monitors.base import BaseMonitor
from sentinel.runner.result import RunResult
from sentinel.runner.runner import run_task
from sentinel.schemas.task import TaskSpec


def run_tasks(
    tasks: Sequence[TaskSpec],
    agent: BaseAgent,
    graders: Sequence[BaseGrader],
    monitors: Sequence[BaseMonitor],
) -> list[RunResult]:
    """Run multiple tasks in input order with the same pipeline.

    Args:
        tasks: Tasks to execute.
        agent: Agent to use for every task.
        graders: Graders to apply to every task run.
        monitors: Monitors to apply to every task run.

    Returns:
        list[RunResult]: Run results in the same order as `tasks`.
    """
    return [
        run_task(
            task=task,
            agent=agent,
            graders=graders,
            monitors=monitors,
        )
        for task in tasks
    ]


def summarize_batch(results: Sequence[RunResult]) -> dict[str, object]:
    """Compute a compact aggregate summary for a batch of runs.

    Args:
        results: Run results to summarize.

    Returns:
        dict[str, object]: Aggregate counts and rates for the batch.
    """
    total_runs = len(results)
    passed_runs = sum(result.all_graders_passed for result in results)
    flagged_runs = sum(result.any_monitor_flagged for result in results)
    failed_runs = total_runs - passed_runs

    pass_rate = passed_runs / total_runs if total_runs else 0.0
    flag_rate = flagged_runs / total_runs if total_runs else 0.0

    return {
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "flagged_runs": flagged_runs,
        "failed_runs": failed_runs,
        "pass_rate": pass_rate,
        "flag_rate": flag_rate,
    }
