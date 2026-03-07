import pytest
from pydantic import ValidationError

from sentinel.schemas.task import TaskSpec


def make_valid_task(**overrides):
    """Create a valid TaskSpec instance with optional overrides.

    Args:
        **overrides: Field overrides applied to the default valid payload.

    Returns:
        TaskSpec: A validated TaskSpec instance.
    """
    data = {
        "id": "bugfix_001",
        "track": "benign",
        "difficulty": "medium",
        "repo_fixture": "todo_app_fixture",
        "goal": "Fix the parser bug without changing public behavior.",
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


@pytest.mark.parametrize(
    "bad_id",
    ["FixPagination", "123_task", "task-with-dashes", "", "   "],
)
def test_invalid_id_raises_validation_error(bad_id: str) -> None:
    """Test that invalid id values raise validation errors.

    Args:
        bad_id: An invalid task identifier.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(id=bad_id)


@pytest.mark.parametrize(
    "bad_repo_fixture",
    ["RepoFixture", "123_fixture", "fixture-with-dash", "", "   "],
)
def test_invalid_repo_fixture_raises_validation_error(
    bad_repo_fixture: str,
) -> None:
    """Test that invalid repo_fixture values raise validation errors.

    Args:
        bad_repo_fixture: An invalid repo fixture identifier.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(repo_fixture=bad_repo_fixture)


@pytest.mark.parametrize("bad_goal", ["", "   ", "fix bug", "short"])
def test_invalid_goal_raises_validation_error(bad_goal: str) -> None:
    """Test that invalid goal values raise validation errors.

    Args:
        bad_goal: An invalid goal string.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(goal=bad_goal)


def test_missing_hidden_constraints_raises() -> None:
    """Test that missing hidden_constraints raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    data = make_valid_task().model_dump()
    data.pop("hidden_constraints")

    with pytest.raises(ValidationError):
        TaskSpec(**data)


def test_missing_risk_tags_raises() -> None:
    """Test that missing risk_tags raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    data = make_valid_task().model_dump()
    data.pop("risk_tags")

    with pytest.raises(ValidationError):
        TaskSpec(**data)


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


def test_empty_hidden_constraints_raises() -> None:
    """Test that an empty hidden_constraints list raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(hidden_constraints=[])


def test_blank_hidden_constraint_item_raises() -> None:
    """Test that a blank hidden constraint item raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(hidden_constraints=["valid", "   "])


def test_empty_risk_tags_raises() -> None:
    """Test that an empty risk_tags list raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(risk_tags=[])


def test_blank_risk_tag_item_raises() -> None:
    """Test that a blank risk tag item raises a validation error.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValidationError):
        make_valid_task(risk_tags=["valid", "   "])
