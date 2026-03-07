from pathlib import Path
from typing import Protocol

from sentinel.grading.result import GraderResult


class BaseGrader(Protocol):
    """Minimal protocol for workspace graders."""

    @property
    def name(self) -> str:
        """Return the grader name."""
        ...

    def grade(self, workspace: Path) -> GraderResult:
        """Grade the given workspace."""
        ...
