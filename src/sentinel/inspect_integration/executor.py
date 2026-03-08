from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinel.agents.base import BaseAgent
from sentinel.grading.base import BaseGrader
from sentinel.inspect_integration.task_stub import InspectTaskStub
from sentinel.monitors.base import BaseMonitor
from sentinel.runner import RunResult, run_task, summarize_batch
from sentinel.schemas.task import TaskSpec
from sentinel.traces.events import validate_non_empty_text


class InspectExecutionResult(BaseModel):
    """Result of executing an Inspect task stub through Sentinel."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    task_name: str
    results: list[RunResult] = Field(default_factory=list)
    batch_summary: dict[str, object] = Field(default_factory=dict)

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, value: str) -> str:
        """Validate the execution task name."""
        return validate_non_empty_text(value)


def execute_inspect_task_stub(
    task_stub: InspectTaskStub,
    tasks_by_id: dict[str, TaskSpec],
    agent: BaseAgent,
    graders: Sequence[BaseGrader],
    monitors: Sequence[BaseMonitor],
) -> InspectExecutionResult:
    """Execute an Inspect task stub through Sentinel's native runner.

    Args:
        task_stub: Inspect-style task package to execute.
        tasks_by_id: Original Sentinel task specs keyed by task id.
        agent: Agent to run for each packaged sample.
        graders: Graders to apply to each run.
        monitors: Monitors to apply to each run.

    Returns:
        InspectExecutionResult: Ordered run results plus batch summary.

    Raises:
        KeyError: If a packaged sample id is missing from `tasks_by_id`.
    """
    results = [
        run_task(
            task=tasks_by_id[sample.id],
            agent=agent,
            graders=graders,
            monitors=monitors,
        )
        for sample in task_stub.samples
    ]

    return InspectExecutionResult(
        task_name=task_stub.name,
        results=results,
        batch_summary=summarize_batch(results),
    )
