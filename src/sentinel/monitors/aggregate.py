from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from sentinel.monitors.base import BaseMonitor
from sentinel.monitors.result import MonitorResult
from sentinel.traces import RunTrace


class MonitorAggregate(BaseModel):
    """Aggregate verdict over multiple monitor results."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    results: list[MonitorResult] = Field(default_factory=list)
    any_flagged: bool = False
    max_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    flagged_monitor_names: list[str] = Field(default_factory=list)


def run_monitors(
    trace: RunTrace,
    monitors: Sequence[BaseMonitor],
) -> MonitorAggregate:
    """Run monitors in order and aggregate their verdicts.

    Args:
        trace: Run trace to assess.
        monitors: Monitors to execute.

    Returns:
        MonitorAggregate: Raw monitor outputs plus aggregate fields.
    """
    results = [monitor.assess(trace) for monitor in monitors]
    flagged_monitor_names = [
        result.monitor_name for result in results if result.suspicious
    ]
    max_confidence = max((result.confidence for result in results), default=0.0)

    return MonitorAggregate(
        results=results,
        any_flagged=bool(flagged_monitor_names),
        max_confidence=max_confidence,
        flagged_monitor_names=flagged_monitor_names,
    )
