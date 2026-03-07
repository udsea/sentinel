from datetime import datetime

import pytest
from pydantic import ValidationError

from sentinel.sandbox import fixture_workspace
from sentinel.traces import FileReadEvent, FileWriteEvent, FinalOutput, RunTrace


def test_create_valid_empty_run_trace() -> None:
    """Test that a valid empty RunTrace can be created."""
    with fixture_workspace("todo_api") as workspace:
        trace = RunTrace(task_id="trace_task", workspace=str(workspace))
        other_trace = RunTrace(task_id="other_task", workspace=str(workspace))

    trace.add_file_read("app.py", "def create_item")

    assert trace.task_id == "trace_task"
    assert trace.workspace
    assert trace.file_writes == []
    assert trace.final_output is None
    assert other_trace.file_reads == []


def test_add_file_read_appends_event() -> None:
    """Test that add_file_read appends a FileReadEvent."""
    with fixture_workspace("todo_api") as workspace:
        trace = RunTrace(task_id="trace_task", workspace=str(workspace))

    trace.add_file_read("app.py", "def create_item")

    assert len(trace.file_reads) == 1
    assert trace.file_reads[0].relative_path == "app.py"
    assert trace.file_reads[0].content_preview == "def create_item"
    assert isinstance(trace.file_reads[0].timestamp, datetime)


def test_add_file_write_appends_event() -> None:
    """Test that add_file_write appends a FileWriteEvent."""
    with fixture_workspace("todo_api") as workspace:
        trace = RunTrace(task_id="trace_task", workspace=str(workspace))

    trace.add_file_write("app.py", "return {'name': 'milk'}")

    assert len(trace.file_writes) == 1
    assert trace.file_writes[0].relative_path == "app.py"
    assert trace.file_writes[0].content_preview == "return {'name': 'milk'}"
    assert isinstance(trace.file_writes[0].timestamp, datetime)


def test_set_final_output_sets_output() -> None:
    """Test that set_final_output stores a FinalOutput."""
    with fixture_workspace("todo_api") as workspace:
        trace = RunTrace(task_id="trace_task", workspace=str(workspace))

    trace.set_final_output("Fixed the todo item normalization bug.")

    assert isinstance(trace.final_output, FinalOutput)
    assert trace.final_output is not None
    assert trace.final_output.text == "Fixed the todo item normalization bug."
    assert isinstance(trace.final_output.timestamp, datetime)


def test_invalid_task_id_fails_validation() -> None:
    """Test that invalid task identifiers are rejected."""
    with fixture_workspace("todo_api") as workspace:
        with pytest.raises(ValidationError, match="must be lowercase"):
            RunTrace(task_id="TraceTask", workspace=str(workspace))


def test_blank_workspace_fails_validation() -> None:
    """Test that blank workspace values are rejected."""
    with pytest.raises(ValidationError, match="must not be blank"):
        RunTrace(task_id="trace_task", workspace="   ")


@pytest.mark.parametrize(
    ("event_type", "relative_path"),
    [
        (FileReadEvent, "/tmp/app.py"),
        (FileWriteEvent, "/tmp/app.py"),
    ],
)
def test_absolute_event_path_fails_validation(
    event_type: type[FileReadEvent] | type[FileWriteEvent],
    relative_path: str,
) -> None:
    """Test that absolute event paths are rejected.

    Args:
        event_type: Event model under test.
        relative_path: Invalid absolute path.
    """
    with pytest.raises(ValidationError, match="must be a relative path"):
        event_type(relative_path=relative_path, content_preview="preview")


@pytest.mark.parametrize(
    ("event_type", "relative_path"),
    [
        (FileReadEvent, "../secret.txt"),
        (FileWriteEvent, "../secret.txt"),
    ],
)
def test_traversal_path_fails_validation(
    event_type: type[FileReadEvent] | type[FileWriteEvent],
    relative_path: str,
) -> None:
    """Test that parent traversal paths are rejected.

    Args:
        event_type: Event model under test.
        relative_path: Invalid traversal path.
    """
    with pytest.raises(ValidationError, match="must not contain parent traversal"):
        event_type(relative_path=relative_path, content_preview="preview")


def test_blank_final_output_fails_validation() -> None:
    """Test that blank final output text is rejected."""
    with fixture_workspace("todo_api") as workspace:
        trace = RunTrace(task_id="trace_task", workspace=str(workspace))

    with pytest.raises(ValidationError, match="must not be blank"):
        trace.set_final_output("   ")
