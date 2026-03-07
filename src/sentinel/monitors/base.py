from typing import Protocol

from sentinel.monitors.result import MonitorResult
from sentinel.traces import RunTrace


class BaseMonitor(Protocol):
    """Minimal protocol for trace monitors."""

    name: str

    def assess(self, trace: RunTrace) -> MonitorResult:
        """Assess a run trace and return a monitor result."""
