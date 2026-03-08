from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel.traces.events import validate_non_empty_text

AgentKind = Literal["benign_scripted", "cheating_scripted", "model"]
AgentProvider = Literal["openai_compatible", "openrouter"]
GraderKind = Literal["file_exists", "file_contains", "pytest"]
MonitorKind = Literal["path_risk", "keyword_risk", "content_risk", "write_policy"]


class AgentSpec(BaseModel):
    """Configuration for selecting and building an agent."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    kind: AgentKind
    model: str | None = None
    base_url: str | None = None
    provider: AgentProvider | None = None

    @field_validator("model", "base_url")
    @classmethod
    def validate_optional_text_fields(cls, value: str | None) -> str | None:
        """Validate optional agent text fields."""
        if value is None:
            return None

        return validate_non_empty_text(value)

    @model_validator(mode="after")
    def validate_model_agent_requirements(self) -> "AgentSpec":
        """Validate model-agent specific requirements."""
        if self.kind != "model":
            return self

        if self.model is None:
            raise ValueError("Model agents require a model name.")

        provider = "openai_compatible" if self.provider is None else self.provider
        if provider == "openai_compatible" and self.base_url is None:
            raise ValueError("OpenAI-compatible model agents require a base_url.")

        return self


class GraderSpec(BaseModel):
    """Configuration for selecting and building a grader."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    kind: GraderKind
    relative_path: str | None = None
    needle: str | None = None
    pytest_args: list[str] = Field(default_factory=list)

    @field_validator("relative_path", "needle")
    @classmethod
    def validate_optional_text_fields(cls, value: str | None) -> str | None:
        """Validate optional grader text fields."""
        if value is None:
            return None

        return validate_non_empty_text(value)

    @model_validator(mode="after")
    def validate_grader_requirements(self) -> "GraderSpec":
        """Validate kind-specific grader requirements."""
        if self.kind == "file_exists" and self.relative_path is None:
            raise ValueError("file_exists graders require a relative_path.")

        if self.kind == "file_contains":
            if self.relative_path is None:
                raise ValueError("file_contains graders require a relative_path.")
            if self.needle is None:
                raise ValueError("file_contains graders require a needle.")

        return self


class MonitorSpec(BaseModel):
    """Configuration for selecting and building a monitor."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    kind: MonitorKind
    protected_prefixes: list[str] = Field(default_factory=list)

    @field_validator("protected_prefixes")
    @classmethod
    def validate_protected_prefixes(cls, value: list[str]) -> list[str]:
        """Validate protected path prefixes."""
        return [validate_non_empty_text(prefix) for prefix in value]


class ExperimentSpec(BaseModel):
    """Top-level experiment configuration."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    name: str
    tasks: list[str] = Field(..., min_length=1)
    agent: AgentSpec
    graders: list[GraderSpec] = Field(default_factory=list)
    monitors: list[MonitorSpec] = Field(default_factory=list)
    output_dir: str

    @field_validator("name", "output_dir")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        """Validate top-level text fields."""
        return validate_non_empty_text(value)

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, value: list[str]) -> list[str]:
        """Validate task-path entries."""
        return [validate_non_empty_text(task_path) for task_path in value]
