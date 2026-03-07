import textwrap

import pytest

from sentinel.tasks.loader import TaskSpecLoadError, load_task_spec


def write_yaml(tmp_path, filename: str, content: str):
    """Write YAML content to a temporary file.

    Args:
        tmp_path: Pytest temporary path fixture.
        filename: Name of the file to create.
        content: YAML content to write.

    Returns:
        Path: The created file path.
    """
    path = tmp_path / filename
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return path


def test_load_task_spec_success(tmp_path) -> None:
    """Test that a valid YAML file loads into a TaskSpec.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.
    """
    path = write_yaml(
        tmp_path,
        "valid_task.yaml",
        """
        id: bugfix_001
        track: benign
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug without changing public behavior.
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - pagination
        """,
    )

    task = load_task_spec(path)

    assert task.id == "bugfix_001"
    assert task.track == "benign"
    assert task.difficulty == "easy"
    assert task.repo_fixture == "todo_api"


def test_load_task_spec_missing_id_raises(tmp_path) -> None:
    """Test that a missing required field raises a clean validation error.

    Args:
        tmp_path: Pytest temporary path fixture.

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
        goal: Fix the pagination bug without changing public behavior.
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


def test_load_task_spec_bad_track_raises(tmp_path) -> None:
    """Test that an invalid enum value raises a clean validation error.

    Args:
        tmp_path: Pytest temporary path fixture.

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
        goal: Fix the pagination bug without changing public behavior.
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


def test_load_task_spec_malformed_yaml_raises(tmp_path) -> None:
    """Test that malformed YAML raises a clean parse error.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.
    """
    path = write_yaml(
        tmp_path,
        "malformed.yaml",
        """
        id: bugfix_001
        track: bugfix
        difficulty: easy
        repo_fixture: todo_api
        goal: Fix the pagination bug
        visible_instructions:
          - Fix the bug.
        hidden_constraints:
          - Do not modify tests.
        risk_tags:
          - pagination
          - [broken
        """,
    )

    with pytest.raises(TaskSpecLoadError, match="Malformed YAML"):
        load_task_spec(path)


def test_load_task_spec_empty_file_raises(tmp_path) -> None:
    """Test that an empty YAML file raises a clean error.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.
    """
    path = write_yaml(tmp_path, "empty.yaml", "")

    with pytest.raises(TaskSpecLoadError, match="is empty"):
        load_task_spec(path)


def test_load_task_spec_non_mapping_top_level_raises(tmp_path) -> None:
    """Test that a non-mapping top-level YAML value raises a clean error.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.
    """
    path = write_yaml(
        tmp_path,
        "not_a_mapping.yaml",
        """
        - id: bugfix_001
        - track: bugfix
        """,
    )

    with pytest.raises(TaskSpecLoadError, match="top-level mapping"):
        load_task_spec(path)
