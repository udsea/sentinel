from pathlib import Path
from typing import Protocol

from sentinel.schemas.task import TaskSpec
from sentinel.traces import RunTrace


class BaseAgent(Protocol):
    """Minimal protocol for workspace agents."""

    @property
    def name(self) -> str:
        """Return the agent name."""
        ...

    def run(self, task: TaskSpec, workspace: Path) -> RunTrace:
        """Run the agent against a workspace and return its trace."""
        ...
