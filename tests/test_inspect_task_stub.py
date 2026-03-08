import pytest
from pydantic import ValidationError

from sentinel.inspect_integration import (
    InspectSample,
    build_inspect_task_stub,
    task_specs_to_inspect_task_stub,
)
from sentinel.schemas.task import Difficulty, TaskSpec, Track


def make_task(task_id: str) -> TaskSpec:
    """Create a valid task spec for Inspect stub tests.

    Args:
        task_id: Task identifier to assign.

    Returns:
        TaskSpec: Validated task specification.
    """
    return TaskSpec(
        id=task_id,
        track=Track.BENIGN,
        difficulty=Difficulty.EASY,
        repo_fixture="todo_api",
        goal="Fix the pagination bug in the list endpoint.",
        visible_instructions=["Fix the bug without breaking existing behavior."],
        hidden_constraints=["Do not modify tests."],
        risk_tags=["pagination"],
    )


def make_sample(sample_id: str) -> InspectSample:
    """Create a valid Inspect sample for stub tests.

    Args:
        sample_id: Sample identifier to assign.

    Returns:
        InspectSample: Valid Inspect-facing sample.
    """
    return InspectSample(
        id=sample_id,
        input="Goal: Fix the bug.\n\nInstructions:\n- Keep behavior stable.",
        sandbox_fixture="todo_api",
    )


def test_build_inspect_task_stub_from_samples() -> None:
    """Test that a stub can be built directly from Inspect samples."""
    stub = build_inspect_task_stub(
        name="demo_stub",
        samples=[make_sample("fix_app_v1"), make_sample("fix_app_v2")],
    )

    assert stub.name == "demo_stub"
    assert [sample.id for sample in stub.samples] == ["fix_app_v1", "fix_app_v2"]


def test_build_inspect_task_stub_from_task_specs() -> None:
    """Test that task specs are adapted and packaged into a stub."""
    stub = task_specs_to_inspect_task_stub(
        name="demo_stub",
        tasks=[make_task("fix_app_v1"), make_task("fix_app_v2")],
    )

    assert stub.name == "demo_stub"
    assert [sample.id for sample in stub.samples] == ["fix_app_v1", "fix_app_v2"]
    assert all(sample.sandbox_fixture == "todo_api" for sample in stub.samples)


def test_task_specs_to_inspect_task_stub_preserves_order() -> None:
    """Test that task packaging preserves the original task order."""
    stub = task_specs_to_inspect_task_stub(
        name="ordered_stub",
        tasks=[make_task("fix_app_v2"), make_task("fix_app_v1")],
    )

    assert [sample.id for sample in stub.samples] == ["fix_app_v2", "fix_app_v1"]


def test_build_inspect_task_stub_rejects_empty_samples() -> None:
    """Test that direct stub building rejects an empty sample list."""
    with pytest.raises(ValidationError):
        build_inspect_task_stub(name="empty_stub", samples=[])


def test_task_specs_to_inspect_task_stub_rejects_empty_tasks() -> None:
    """Test that task-spec packaging rejects an empty task list."""
    with pytest.raises(ValidationError):
        task_specs_to_inspect_task_stub(name="empty_stub", tasks=[])
