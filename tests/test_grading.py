import pytest

from sentinel.grading import FileContainsGrader, FileExistsGrader, GraderResult
from sentinel.sandbox import fixture_workspace


def test_grader_result_uses_safe_default_dicts() -> None:
    """Test that GraderResult default dictionaries are not shared."""
    first = GraderResult(
        grader_name="first",
        passed=True,
        message="ok",
    )
    second = GraderResult(
        grader_name="second",
        passed=False,
        message="nope",
    )

    first.metadata["key"] = "value"
    first.artifacts["artifact"] = "debug"

    assert second.metadata == {}
    assert second.artifacts == {}


def test_file_exists_grader_passes_for_existing_file() -> None:
    """Test that FileExistsGrader passes when the file exists."""
    grader = FileExistsGrader(relative_path="app.py")

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert isinstance(result, GraderResult)
    assert result.passed is True
    assert result.message == "File exists: app.py"
    assert result.metadata["relative_path"] == "app.py"


def test_file_exists_grader_fails_for_missing_file() -> None:
    """Test that FileExistsGrader fails when the file is missing."""
    grader = FileExistsGrader(relative_path="missing.py")

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert isinstance(result, GraderResult)
    assert result.passed is False
    assert result.message == "File not found: missing.py"
    assert result.metadata["relative_path"] == "missing.py"


def test_file_exists_grader_rejects_absolute_path() -> None:
    """Test that FileExistsGrader rejects absolute grader paths."""
    with pytest.raises(ValueError, match="Grader path must be relative"):
        FileExistsGrader(relative_path="/tmp/app.py")


def test_file_contains_grader_passes_when_text_is_present() -> None:
    """Test that FileContainsGrader passes when the substring is present."""
    grader = FileContainsGrader(
        relative_path="app.py",
        needle="def create_item",
    )

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert isinstance(result, GraderResult)
    assert result.passed is True
    assert result.message == "Substring found in app.py"
    assert result.metadata["needle"] == "def create_item"


def test_file_contains_grader_fails_when_text_is_absent() -> None:
    """Test that FileContainsGrader fails when the substring is absent."""
    grader = FileContainsGrader(
        relative_path="app.py",
        needle="def delete_item",
    )

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert isinstance(result, GraderResult)
    assert result.passed is False
    assert result.message == "Substring not found in app.py"
    assert result.metadata["needle"] == "def delete_item"


def test_file_contains_grader_fails_cleanly_when_file_is_missing() -> None:
    """Test that FileContainsGrader fails cleanly when the file is missing."""
    grader = FileContainsGrader(
        relative_path="missing.py",
        needle="anything",
    )

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert isinstance(result, GraderResult)
    assert result.passed is False
    assert result.message == "File not found: missing.py"
    assert result.metadata["relative_path"] == "missing.py"
    assert result.metadata["needle"] == "anything"


def test_file_contains_grader_rejects_absolute_path() -> None:
    """Test that FileContainsGrader rejects absolute grader paths."""
    with pytest.raises(ValueError, match="Grader path must be relative"):
        FileContainsGrader(relative_path="/tmp/app.py", needle="hello")


def test_file_contains_grader_supports_nested_relative_paths() -> None:
    """Test that FileContainsGrader can inspect nested files in a workspace."""
    grader = FileContainsGrader(
        relative_path="tests/test_app.py",
        needle="create_item",
    )

    with fixture_workspace("todo_api") as workspace:
        result = grader.grade(workspace)

    assert result.passed is True
    assert result.message == "Substring found in tests/test_app.py"
