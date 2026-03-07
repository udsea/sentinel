from collections.abc import Sequence

from sentinel.agents.base import BaseAgent
from sentinel.grading.base import BaseGrader
from sentinel.monitors.base import BaseMonitor
from sentinel.runner.result import RunResult
from sentinel.sandbox import fixture_workspace
from sentinel.schemas.task import TaskSpec


def run_task(
    task: TaskSpec,
    agent: BaseAgent,
    graders: Sequence[BaseGrader],
    monitors: Sequence[BaseMonitor],
) -> RunResult:
    """Run a task end-to-end in an isolated workspace.

    Args:
        task: Task specification describing the fixture to materialize.
        agent: Agent to run against the workspace.
        graders: Graders to execute after the agent run.
        monitors: Monitors to execute against the produced trace.

    Returns:
        RunResult: Structured result for the completed run.
    """
    with fixture_workspace(task.repo_fixture) as workspace:
        trace = agent.run(task_id=task.id, workspace=workspace)
        grader_results = [grader.grade(workspace) for grader in graders]
        monitor_results = [monitor.assess(trace) for monitor in monitors]
        agent_name = agent.name
        workspace_str = str(workspace)

    return RunResult(
        task_id=task.id,
        agent_name=agent_name,
        workspace=workspace_str,
        trace=trace,
        grader_results=grader_results,
        monitor_results=monitor_results,
    )
