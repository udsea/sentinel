import subprocess

import pytest

from sentinel.grading import GraderResult, PytestGrader
from sentinel.sandbox import fixture_workspace


def test_passing_pytest_run_returns_passed_true() -> None:
    """Test that PytestGrader passes when workspace tests pass."""
    grader = PytestGrader(relative_path="tests", pytest_args=["-q"])

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert isinstance(result, GraderResult)
    assert result.passed is True
    assert result.message == "Pytest passed for tests"
    assert result.metadata["relative_path"] == "tests"
    assert result.metadata["returncode"] == 0


def test_failing_pytest_run_returns_failed_result() -> None:
    """Test that PytestGrader fails cleanly when workspace tests fail."""
    grader = PytestGrader(relative_path="tests", pytest_args=["-q"])

    with fixture_workspace("failing_api") as workspace:
        result = grader.grade(workspace)

    assert result.passed is False
    assert result.message == "Pytest failed for tests"
    assert result.metadata["returncode"] != 0


def test_missing_target_returns_failed_result() -> None:
    """Test that missing pytest targets return failed results."""
    grader = PytestGrader(relative_path="missing_tests")

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert result.passed is False
    assert result.message == "Pytest target not found: missing_tests"
    assert result.metadata["returncode"] is None
    assert result.artifacts["stdout"] == ""
    assert result.artifacts["stderr"] == ""


def test_absolute_path_rejected() -> None:
    """Test that absolute pytest targets are rejected up front."""
    with pytest.raises(ValueError, match="relative path"):
        PytestGrader(relative_path="/tmp/tests")


def test_traversal_path_rejected() -> None:
    """Test that parent traversal pytest targets are rejected up front."""
    with pytest.raises(ValueError, match="parent traversal"):
        PytestGrader(relative_path="../tests")


def test_result_includes_stdout_stderr_and_returncode() -> None:
    """Test that subprocess outputs and return codes are preserved."""
    grader = PytestGrader(relative_path="tests", pytest_args=["-q"])

    with fixture_workspace("failing_api") as workspace:
        result = grader.grade(workspace)

    assert result.metadata["returncode"] != 0
    assert isinstance(result.artifacts["stdout"], str)
    assert isinstance(result.artifacts["stderr"], str)
    assert "failed" in result.artifacts["stdout"].lower()


def test_timeout_is_handled_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that pytest subprocess timeouts become failed results."""
    grader = PytestGrader(relative_path="tests")

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=["pytest", "tests"],
            timeout=10,
            output="partial stdout",
            stderr="partial stderr",
        )

    monkeypatch.setattr("sentinel.grading.pytest_grader.subprocess.run", fake_run)

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert result.passed is False
    assert result.message == "Pytest timed out for tests"
    assert result.metadata["returncode"] is None
    assert result.artifacts["stdout"] == "partial stdout"
    assert result.artifacts["stderr"] == "partial stderr"
