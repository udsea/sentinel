from dataclasses import dataclass
from pathlib import Path

from sentinel.grading.result import GraderResult


@dataclass(frozen=True, slots=True)
class FileExistsGrader:
    """Grade whether a relative path exists in a workspace."""

    relative_path: str

    def __post_init__(self) -> None:
        """Validate grader configuration."""
        _validate_relative_path(self.relative_path)

    @property
    def name(self) -> str:
        """Return the grader name."""
        return self.__class__.__name__

    def grade(self, workspace: Path) -> GraderResult:
        """Check whether the configured path exists in the workspace.

        Args:
            workspace: Workspace directory to inspect.

        Returns:
            GraderResult: Grading outcome.
        """
        target_path = workspace / self.relative_path
        exists = target_path.exists()

        return GraderResult(
            grader_name=self.name,
            passed=exists,
            message=(
                f"File exists: {self.relative_path}"
                if exists
                else f"File not found: {self.relative_path}"
            ),
            metadata={
                "relative_path": self.relative_path,
                "checked_path": str(target_path),
            },
        )


@dataclass(frozen=True, slots=True)
class FileContainsGrader:
    """Grade whether a file contains a substring."""

    relative_path: str
    needle: str

    def __post_init__(self) -> None:
        """Validate grader configuration."""
        _validate_relative_path(self.relative_path)

    @property
    def name(self) -> str:
        """Return the grader name."""
        return self.__class__.__name__

    def grade(self, workspace: Path) -> GraderResult:
        """Check whether the configured file contains the configured text.

        Args:
            workspace: Workspace directory to inspect.

        Returns:
            GraderResult: Grading outcome.
        """
        target_path = workspace / self.relative_path

        if not target_path.exists():
            return GraderResult(
                grader_name=self.name,
                passed=False,
                message=f"File not found: {self.relative_path}",
                metadata={
                    "relative_path": self.relative_path,
                    "checked_path": str(target_path),
                    "needle": self.needle,
                },
            )

        if not target_path.is_file():
            return GraderResult(
                grader_name=self.name,
                passed=False,
                message=f"Path is not a file: {self.relative_path}",
                metadata={
                    "relative_path": self.relative_path,
                    "checked_path": str(target_path),
                    "needle": self.needle,
                },
            )

        contents = target_path.read_text(encoding="utf-8")
        passed = self.needle in contents

        return GraderResult(
            grader_name=self.name,
            passed=passed,
            message=(
                f"Substring found in {self.relative_path}"
                if passed
                else f"Substring not found in {self.relative_path}"
            ),
            metadata={
                "relative_path": self.relative_path,
                "checked_path": str(target_path),
                "needle": self.needle,
            },
        )


def _validate_relative_path(relative_path: str) -> None:
    """Validate grader relative path input.

    Args:
        relative_path: Relative path configured for the grader.

    Raises:
        TypeError: If the provided path is not a string.
        ValueError: If the provided path is blank, absolute, or escapes the
            workspace.
    """
    if not isinstance(relative_path, str):
        raise TypeError("Grader path must be a string.")

    normalized_path = relative_path.strip()
    if not normalized_path:
        raise ValueError("Grader path must not be blank.")

    path = Path(normalized_path)
    if path.is_absolute():
        raise ValueError(f"Grader path must be relative: '{relative_path}'.")

    if ".." in path.parts:
        raise ValueError(
            f"Grader path must stay within the workspace: '{relative_path}'."
        )
