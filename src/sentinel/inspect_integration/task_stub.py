from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinel.inspect_integration.sample import InspectSample
from sentinel.inspect_integration.task_adapter import task_spec_to_inspect_sample
from sentinel.schemas.task import TaskSpec
from sentinel.traces.events import validate_non_empty_text


class InspectTaskStub(BaseModel):
    """Inspect-facing container for one or more adapted Sentinel samples."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    name: str
    samples: list[InspectSample] = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate the stub name."""
        return validate_non_empty_text(value)


def build_inspect_task_stub(
    name: str,
    samples: Sequence[InspectSample],
) -> InspectTaskStub:
    """Package Inspect samples into a task-like container.

    Args:
        name: Inspect-facing task stub name.
        samples: Samples to package in order.

    Returns:
        InspectTaskStub: Validated Inspect task stub.
    """
    return InspectTaskStub(name=name, samples=list(samples))


def task_specs_to_inspect_task_stub(
    name: str,
    tasks: Sequence[TaskSpec],
) -> InspectTaskStub:
    """Convert Sentinel task specs into an Inspect task stub.

    Args:
        name: Inspect-facing task stub name.
        tasks: Sentinel task specs to adapt and package.

    Returns:
        InspectTaskStub: Validated Inspect task stub with adapted samples.
    """
    return build_inspect_task_stub(
        name=name,
        samples=[task_spec_to_inspect_sample(task) for task in tasks],
    )
