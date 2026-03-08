import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from sentinel.agents.base import BaseAgent
from sentinel.agents.model import BaseTextModelClient, build_agent_prompt
from sentinel.schemas.task import TaskSpec
from sentinel.traces import RunTrace
from sentinel.traces.events import (
    validate_non_empty_text,
    validate_relative_path,
)

_READ_ACTION = "read_file"
_WRITE_ACTION = "write_file"
_FINAL_ACTION = "final"
_DEFAULT_MAX_STEPS = 3


class ModelAction(BaseModel):
    """Structured action emitted by a bounded action-taking model agent."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    action: Literal["read_file", "write_file", "final"]
    path: str | None = None
    content: str | None = None
    text: str | None = None

    @field_validator("path")
    @classmethod
    def validate_optional_path(cls, value: str | None) -> str | None:
        """Validate the optional action path."""
        if value is None:
            return None

        return validate_relative_path(value)

    @field_validator("text")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """Validate optional non-empty text fields."""
        if value is None:
            return None

        return validate_non_empty_text(value)

    @field_validator("content")
    @classmethod
    def validate_optional_content(cls, value: str | None) -> str | None:
        """Validate optional write content without stripping it."""
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError("must be a string")

        if not value.strip():
            raise ValueError("must not be blank")

        return value

    @model_validator(mode="after")
    def validate_action_fields(self) -> "ModelAction":
        """Validate the fields required by each action kind."""
        if self.action == _READ_ACTION:
            if self.path is None:
                raise ValueError("read_file actions require a path")
            if self.content is not None or self.text is not None:
                raise ValueError("read_file actions may only include path")
            return self

        if self.action == _WRITE_ACTION:
            if self.path is None:
                raise ValueError("write_file actions require a path")
            if self.content is None:
                raise ValueError("write_file actions require content")
            if self.text is not None:
                raise ValueError("write_file actions may not include text")
            return self

        if self.path is not None or self.content is not None:
            raise ValueError("final actions may only include text")
        if self.text is None:
            raise ValueError("final actions require text")

        return self

    @classmethod
    def parse_response(cls, response: str) -> "ModelAction":
        """Parse a model response into a validated action.

        Args:
            response: Raw model response that should contain one JSON object.

        Returns:
            ModelAction: Validated structured action.

        Raises:
            ValueError: If the response is not valid JSON or not a JSON object.
        """
        normalized_response = _strip_json_code_fence(response)
        try:
            payload = json.loads(normalized_response)
        except json.JSONDecodeError as error:
            raise ValueError("Model response was not valid JSON.") from error

        if not isinstance(payload, dict):
            raise ValueError("Model response must decode to a JSON object.")

        return cls.model_validate(payload)


class ActionModelAgent(BaseAgent):
    """Bounded action-taking model agent with a tiny JSON action protocol."""

    def __init__(
        self,
        client: BaseTextModelClient,
        name: str | None = None,
        max_steps: int = _DEFAULT_MAX_STEPS,
    ) -> None:
        """Initialize the bounded action-taking model agent.

        Args:
            client: Text-generation client to call for each step.
            name: Optional explicit agent name.
            max_steps: Maximum number of JSON actions to execute.
        """
        self.client = client
        self._name = name
        self.max_steps = _validate_max_steps(max_steps)

    @property
    def name(self) -> str:
        """Return the configured or derived agent name."""
        if self._name is not None:
            return self._name

        return f"action_model_agent:{self.client.name}"

    def run(self, task: TaskSpec, workspace: Path) -> RunTrace:
        """Run the bounded action loop for a task.

        Args:
            task: Task specification to render for the model client.
            workspace: Workspace directory for trace context.

        Returns:
            RunTrace: Trace containing file events and a final output.

        Raises:
            RuntimeError: If the model does not produce a final action in time.
            ValueError: If the model emits an invalid action.
        """
        trace = RunTrace(task_id=task.id, workspace=str(workspace))
        history: list[str] = []

        for step_number in range(1, self.max_steps + 1):
            prompt = _build_action_prompt(
                task=task,
                history=history,
                step_number=step_number,
                max_steps=self.max_steps,
            )
            action = ModelAction.parse_response(self.client.generate(prompt))

            if action.action == _READ_ACTION:
                assert action.path is not None
                contents = _read_workspace_file(workspace, action.path)
                trace.add_file_read(action.path, contents)
                history.append(
                    f"Step {step_number}: read_file {action.path}\n"
                    f"Contents:\n{contents}"
                )
                continue

            if action.action == _WRITE_ACTION:
                assert action.path is not None
                assert action.content is not None
                _write_workspace_file(workspace, action.path, action.content)
                trace.add_file_write(action.path, action.content)
                history.append(
                    f"Step {step_number}: write_file {action.path}\nWrote:\n"
                    f"{action.content}"
                )
                continue

            assert action.text is not None
            trace.set_final_output(action.text)
            return trace

        raise RuntimeError(
            "ActionModelAgent did not receive a final action within "
            f"{self.max_steps} steps."
        )


def _build_action_prompt(
    *,
    task: TaskSpec,
    history: list[str],
    step_number: int,
    max_steps: int,
) -> str:
    """Build the bounded-action prompt for one loop iteration.

    Args:
        task: Task specification being executed.
        history: Prior actions and observations.
        step_number: Current action step number.
        max_steps: Maximum allowed action steps.

    Returns:
        str: Deterministic prompt text for the current step.
    """
    lines = [
        build_agent_prompt(task),
        "",
        "You must respond with exactly one JSON object for the next action.",
        "Allowed actions:",
        '{"action":"read_file","path":"relative/path.py"}',
        '{"action":"write_file","path":"relative/path.py",'
        '"content":"full file contents"}',
        '{"action":"final","text":"short final answer"}',
        "",
        "Rules:",
        "- Use only relative paths inside the workspace.",
        "- Allowed actions are read_file, write_file, and final.",
        "- Do not call shell commands or invent tools.",
        f"- You have at most {max_steps} total steps.",
        f"- This is step {step_number} of {max_steps}.",
    ]

    if history:
        lines.extend(
            [
                "",
                "Previous actions and observations:",
                *history,
            ]
        )

    return "\n".join(lines).strip()


def _validate_max_steps(max_steps: int) -> int:
    """Validate the configured action-step limit.

    Args:
        max_steps: Requested maximum number of steps.

    Returns:
        int: Validated step limit.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the limit is outside the supported range.
    """
    if not isinstance(max_steps, int):
        raise TypeError("max_steps must be an integer.")

    if max_steps < 1 or max_steps > _DEFAULT_MAX_STEPS:
        raise ValueError("max_steps must be between 1 and 3.")

    return max_steps


def _read_workspace_file(workspace: Path, relative_path: str) -> str:
    """Read a workspace file as UTF-8 text.

    Args:
        workspace: Workspace directory.
        relative_path: Relative file path within the workspace.

    Returns:
        str: File contents.
    """
    return (workspace / relative_path).read_text(encoding="utf-8")


def _write_workspace_file(workspace: Path, relative_path: str, contents: str) -> None:
    """Write UTF-8 text to a workspace file.

    Args:
        workspace: Workspace directory.
        relative_path: Relative file path within the workspace.
        contents: File contents to write.
    """
    target_path = workspace / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(contents, encoding="utf-8")


def _strip_json_code_fence(response: str) -> str:
    """Strip a surrounding fenced JSON block if present.

    Args:
        response: Raw model response.

    Returns:
        str: Response text without a surrounding Markdown code fence.
    """
    normalized_response = validate_non_empty_text(response)
    if not normalized_response.startswith("```"):
        return normalized_response

    lines = normalized_response.splitlines()
    if len(lines) < 3:
        return normalized_response

    if not lines[-1].strip().startswith("```"):
        return normalized_response

    return "\n".join(lines[1:-1]).strip()
