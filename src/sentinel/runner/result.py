from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel.grading.result import GraderResult
from sentinel.monitors.aggregate import MonitorAggregate
from sentinel.monitors.result import MonitorResult
from sentinel.traces import RunTrace
from sentinel.traces.events import validate_non_empty_text


class RunResult(BaseModel):
    """Structured result for a single task run."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    task_id: str
    agent_name: str
    workspace: str
    trace: RunTrace
    grader_results: list[GraderResult] = Field(default_factory=list)
    monitor_results: list[MonitorResult] = Field(default_factory=list)
    monitor_aggregate: MonitorAggregate = Field(default_factory=MonitorAggregate)

    @field_validator("task_id", "agent_name", "workspace")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        """Validate text fields on the run result."""
        return validate_non_empty_text(value)

    @model_validator(mode="after")
    def validate_trace_alignment(self) -> "RunResult":
        """Ensure top-level fields stay aligned with the trace."""
        if self.task_id != self.trace.task_id:
            raise ValueError("RunResult task_id must match trace.task_id")

        if self.workspace != self.trace.workspace:
            raise ValueError("RunResult workspace must match trace.workspace")

        if self.monitor_results != self.monitor_aggregate.results:
            raise ValueError(
                "RunResult monitor_results must match monitor_aggregate.results"
            )

        return self

    @property
    def all_graders_passed(self) -> bool:
        """Return whether every grader passed."""
        return all(result.passed for result in self.grader_results)

    @property
    def any_monitor_flagged(self) -> bool:
        """Return whether any monitor marked the run as suspicious."""
        return self.monitor_aggregate.any_flagged
