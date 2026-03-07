from pathlib import Path
from typing import Protocol

from sentinel.traces import RunTrace


class BaseAgent(Protocol):
    """Minimal protocol for deterministic workspace agents."""

    name: str

    def run(self, task_id: str, workspace: Path) -> RunTrace:
        """Run the agent against a workspace and return its trace."""
