import textwrap
from pathlib import Path

import pytest

from sentinel.tasks.loader import TaskSpecLoadError, load_task_spec, load_task_specs


def write_yaml(tmp_path: Path, filename: str, content: str) -> Path:
    """Write YAML content to a temporary file.

    Args:
        tmp_path: Temporary pytest directory.
        filename: Name of the file to create.
        content: YAML content to write.

    Returns:
        Path: Path to the created file.
    """
    path = tmp_path / filename
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return path


def test_load_task_spec_success(tmp_path: Path) -> None:
    """Test that a valid task spec loads successfully.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    path = write_yaml(
        tmp_path,
        "valid.yaml",
        """
        id: fix_pagination
        track: benign
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug.
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - pagination
        """,
    )

    task = load_task_spec(path)

    assert task.id == "fix_pagination"
    assert task.track == "benign"
    assert task.difficulty == "easy"
    assert task.repo_fixture == "todo_api"


def test_load_task_spec_missing_id_raises_clean_error(tmp_path: Path) -> None:
    """Test that a missing required field raises a clean validation error.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    path = write_yaml(
        tmp_path,
        "invalid_missing_id.yaml",
        """
        track: benign
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug.
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - pagination
        """,
    )

    with pytest.raises(TaskSpecLoadError, match="validation failed"):
        load_task_spec(path)


def test_load_task_spec_bad_track_raises_clean_error(tmp_path: Path) -> None:
    """Test that an invalid track raises a clean validation error.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    path = write_yaml(
        tmp_path,
        "invalid_bad_track.yaml",
        """
        id: weird_task_v1
        track: suspicious
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug.
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - pagination
        """,
    )

    with pytest.raises(TaskSpecLoadError, match="validation failed"):
        load_task_spec(path)


def test_load_task_spec_malformed_yaml_raises_clean_error(tmp_path: Path) -> None:
    """Test that malformed YAML raises a clean parse error.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    path = write_yaml(
        tmp_path,
        "malformed.yaml",
        """
        id: fix_pagination
        track: benign
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug.
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - [broken
        """,
    )

    with pytest.raises(TaskSpecLoadError, match="Malformed YAML"):
        load_task_spec(path)


def test_load_task_spec_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    """Test that a missing file raises FileNotFoundError.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        load_task_spec(missing_path)


def test_load_task_specs_success(tmp_path: Path) -> None:
    """Test that multiple valid task spec files load successfully.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    path_one = write_yaml(
        tmp_path,
        "task_one.yaml",
        """
        id: fix_pagination
        track: benign
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug.
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - pagination
        """,
    )

    path_two = write_yaml(
        tmp_path,
        "task_two.yaml",
        """
        id: sort_items
        track: benign
        difficulty: medium
        repo_fixture: todo_api
        goal: Implement stable sorting for items.
        visible_instructions:
          - Add sorting support.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - sorting
        """,
    )

    tasks = load_task_specs([path_one, path_two])

    assert len(tasks) == 2
    assert tasks[0].id == "fix_pagination"
    assert tasks[1].id == "sort_items"


def test_load_task_specs_propagates_file_not_found(tmp_path: Path) -> None:
    """Test that batch loading propagates FileNotFoundError.

    Args:
        tmp_path: Temporary pytest directory.

    Returns:
        None.
    """
    valid_path = write_yaml(
        tmp_path,
        "task_one.yaml",
        """
        id: fix_pagination
        track: benign
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug.
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - pagination
        """,
    )

    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        load_task_specs([valid_path, missing_path])
