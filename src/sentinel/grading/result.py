from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraderResult(BaseModel):
    """Structured result returned by a grader."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    grader_name: str
    passed: bool
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, Any] = Field(default_factory=dict)
