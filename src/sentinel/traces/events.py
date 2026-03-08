from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def validate_non_empty_text(value: str) -> str:
    """Validate that a text field is a non-empty string.

    Args:
        value: Text value to validate.

    Returns:
        str: Normalized text value.

    Raises:
        TypeError: If the value is not a string.
        ValueError: If the value is blank after trimming.
    """
    if not isinstance(value, str):
        raise TypeError("must be a string")

    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError("must not be blank")

    return normalized_value


def validate_relative_path(value: str) -> str:
    """Validate that a path is relative and stays inside the workspace.

    Args:
        value: Relative path to validate.

    Returns:
        str: Normalized relative path.

    Raises:
        TypeError: If the value is not a string.
        ValueError: If the path is blank, absolute, or contains parent
            traversal.
    """
    normalized_value = validate_non_empty_text(value)
    path = Path(normalized_value)

    if path.is_absolute():
        raise ValueError("must be a relative path")

    if ".." in path.parts:
        raise ValueError("must not contain parent traversal")

    return normalized_value


class _BaseFileEvent(BaseModel):
    """Common fields and validation for file trace events."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    relative_path: str
    content_preview: str
    timestamp: datetime = Field(default_factory=_utc_now)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path_field(cls, value: str) -> str:
        """Validate the event relative path."""
        return validate_relative_path(value)

    @field_validator("content_preview")
    @classmethod
    def validate_content_preview(cls, value: str) -> str:
        """Validate the content preview field."""
        return validate_non_empty_text(value)


class FileReadEvent(_BaseFileEvent):
    """Trace event for a file read."""


class FileWriteEvent(_BaseFileEvent):
    """Trace event for a file write."""


class FinalOutput(BaseModel):
    """Final user-visible output for a run."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    text: str
    timestamp: datetime = Field(default_factory=_utc_now)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Validate final output text."""
        return validate_non_empty_text(value)
