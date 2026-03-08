import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from sentinel.grading.result import GraderResult
from sentinel.traces.events import validate_relative_path

_PYTEST_TIMEOUT_SECONDS = 10


@dataclass(frozen=True, slots=True)
class PytestGrader:
    """Grade a workspace by running pytest inside it."""

    relative_path: str = "."
    pytest_args: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate grader configuration."""
        object.__setattr__(
            self, "relative_path", validate_relative_path(self.relative_path)
        )
        _validate_pytest_args(self.pytest_args)

    @property
    def name(self) -> str:
        """Return the grader name."""
        return self.__class__.__name__

    def grade(self, workspace: Path) -> GraderResult:
        """Run pytest inside the workspace and capture the result.

        Args:
            workspace: Workspace directory to test.

        Returns:
            GraderResult: Structured pytest grading outcome.
        """
        target_path = workspace / self.relative_path

        if not target_path.exists():
            return GraderResult(
                grader_name=self.name,
                passed=False,
                message=f"Pytest target not found: {self.relative_path}",
                metadata={
                    "relative_path": self.relative_path,
                    "returncode": None,
                    "checked_path": str(target_path),
                },
                artifacts={"stdout": "", "stderr": ""},
            )

        command = [
            sys.executable,
            "-m",
            "pytest",
            self.relative_path,
            *self.pytest_args,
        ]

        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=_PYTEST_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            return GraderResult(
                grader_name=self.name,
                passed=False,
                message=f"Pytest timed out for {self.relative_path}",
                metadata={
                    "relative_path": self.relative_path,
                    "returncode": None,
                },
                artifacts={
                    "stdout": _normalize_subprocess_output(error.stdout),
                    "stderr": _normalize_subprocess_output(error.stderr),
                },
            )

        passed = completed.returncode == 0
        return GraderResult(
            grader_name=self.name,
            passed=passed,
            message=(
                f"Pytest passed for {self.relative_path}"
                if passed
                else f"Pytest failed for {self.relative_path}"
            ),
            metadata={
                "relative_path": self.relative_path,
                "returncode": completed.returncode,
            },
            artifacts={
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
        )


def _validate_pytest_args(pytest_args: list[str]) -> None:
    """Validate pytest argument configuration.

    Args:
        pytest_args: Additional pytest arguments.

    Raises:
        TypeError: If the value is not a list of strings.
    """
    if not isinstance(pytest_args, list):
        raise TypeError("Pytest args must be provided as a list of strings.")

    for argument in pytest_args:
        if not isinstance(argument, str):
            raise TypeError("Pytest args must be strings.")


def _normalize_subprocess_output(output: str | bytes | None) -> str:
    """Normalize subprocess output to UTF-8 text.

    Args:
        output: Raw subprocess output value.

    Returns:
        str: Normalized text output.
    """
    if output is None:
        return ""

    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")

    return output
