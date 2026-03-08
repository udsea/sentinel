from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinel.traces.events import validate_non_empty_text


class InspectSample(BaseModel):
    """Minimal Inspect-facing sample payload produced by Sentinel."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    id: str
    input: str
    metadata: dict[str, object] = Field(default_factory=dict)
    sandbox_fixture: str

    @field_validator("id", "input", "sandbox_fixture")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        """Validate required text fields."""
        return validate_non_empty_text(value)
