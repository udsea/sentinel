from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinel.traces.events import validate_non_empty_text


class MonitorResult(BaseModel):
    """Structured result returned by a run monitor."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    monitor_name: str
    suspicious: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("monitor_name")
    @classmethod
    def validate_monitor_name(cls, value: str) -> str:
        """Validate the monitor name."""
        return validate_non_empty_text(value)

    @field_validator("reasons")
    @classmethod
    def validate_reasons(cls, value: list[str]) -> list[str]:
        """Validate reason strings."""
        return [validate_non_empty_text(reason) for reason in value]
