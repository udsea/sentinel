from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinel.schemas.task import _IDENTIFIER_RE
from sentinel.traces.events import (
    FileReadEvent,
    FileWriteEvent,
    FinalOutput,
    validate_non_empty_text,
)


class RunTrace(BaseModel):
    """Normalized internal trace for a single run."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    task_id: str
    workspace: str
    file_reads: list[FileReadEvent] = Field(default_factory=list)
    file_writes: list[FileWriteEvent] = Field(default_factory=list)
    final_output: FinalOutput | None = None

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        """Validate the task identifier."""
        normalized_value = validate_non_empty_text(value)
        if not _IDENTIFIER_RE.fullmatch(normalized_value):
            raise ValueError(
                "must be lowercase, start with a letter, and contain only "
                "letters, digits, and underscores"
            )

        return normalized_value

    @field_validator("workspace")
    @classmethod
    def validate_workspace(cls, value: str) -> str:
        """Validate the workspace field."""
        return validate_non_empty_text(value)

    def add_file_read(self, relative_path: str, content_preview: str) -> None:
        """Append a file read event to the trace.

        Args:
            relative_path: Relative path that was read.
            content_preview: Short preview of the file contents.
        """
        self.file_reads.append(
            FileReadEvent(
                relative_path=relative_path,
                content_preview=content_preview,
            )
        )

    def add_file_write(self, relative_path: str, content_preview: str) -> None:
        """Append a file write event to the trace.

        Args:
            relative_path: Relative path that was written.
            content_preview: Short preview of the written contents.
        """
        self.file_writes.append(
            FileWriteEvent(
                relative_path=relative_path,
                content_preview=content_preview,
            )
        )

    def set_final_output(self, text: str) -> None:
        """Set the final output for the trace.

        Args:
            text: Final user-visible output text.
        """
        self.final_output = FinalOutput(text=text)
