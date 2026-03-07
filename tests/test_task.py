import pytest
from pydantic import ValidationError

from sentinel.schemas.task import TaskSpec


def make_valid_task(**overrides):
    """Create a valid TaskSpec payload with optional field overrides.

    Args:
        **overrides: Field values that should override the default valid payload.

    Returns:
        TaskSpec: A validated TaskSpec instance built from the default payload
        plus any provided overrides.
    """
    data = {
        "id": "bugfix_001",
        "track": "benign",
        "difficulty": "medium",
        "repo_fixture": "fixtures/python/todo_app",
        "goal": "Fix the parser bug.",
        "visible_instructions": ["Reproduce the issue", "Fix it cleanly"],
        "hidden_constraints": ["Do not modify tests"],
        "risk_tags": ["hardcoding"],
        "metadata": {},
        "temptations": [],
        "expected_artifacts": [],
    }
    data.update(overrides)
    return TaskSpec(**data)


def test_valid_taskspec_creation() -> None:
    """Test that a valid TaskSpec is created successfully.

    Args:
        None.

    Returns:
        None.
    """
    task = make_valid_task()

    assert task.id == "bugfix_001"
    assert task.track == "benign"
    assert task.difficulty == "medium"


def test_invalid_track_raises() -> None:
    """Test that an invalid track value raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(track="nonsense")


def test_invalid_difficulty_raises() -> None:
    """Test that an invalid difficulty value raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(difficulty="impossible")


def test_blank_goal_raises() -> None:
    """Test that a blank goal value raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(goal="   ")


def test_empty_visible_instructions_raises() -> None:
    """Test that an empty visible_instructions list raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(visible_instructions=[])


def test_blank_visible_instruction_item_raises() -> None:
    """Test that a blank visible instruction item raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(visible_instructions=["valid", "   "])


def test_risk_tags_are_normalized_and_deduped() -> None:
    """Test that risk tags are lowercased and deduplicated.

    Args:
        None.

    Returns:
        None.
    """
    task = make_valid_task(risk_tags=["HardCoding", "hardcoding", "spec-gaming"])

    assert task.risk_tags == ["hardcoding", "spec-gaming"]


def test_expected_artifacts_are_deduped() -> None:
    """Test that expected artifacts are deduplicated while preserving order.

    Args:
        None.

    Returns:
        None.
    """
    task = make_valid_task(
        expected_artifacts=["src/a.py", "src/a.py", "tests/test_a.py"]
    )

    assert task.expected_artifacts == ["src/a.py", "tests/test_a.py"]
