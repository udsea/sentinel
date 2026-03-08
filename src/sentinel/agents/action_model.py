import json
import re
from pathlib import Path
from typing import Literal, NoReturn

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


class ActionModelAgentError(RuntimeError):
    """Raised when the bounded action loop fails after a trace has started."""

    def __init__(self, message: str, trace: RunTrace) -> None:
        """Store the failure message and the trace captured so far.

        Args:
            message: Failure message for the exception.
            trace: Trace accumulated before the failure.
        """
        super().__init__(message)
        self.trace = trace


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
        normalized_response = validate_non_empty_text(response)

        try:
            payload = _extract_json_object_payload(normalized_response)
        except ValueError:
            payload = _extract_relaxed_action_payload(normalized_response)

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
            try:
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
            except ActionModelAgentError:
                raise
            except Exception as error:
                _raise_action_model_agent_error(trace, str(error), cause=error)

        _raise_action_model_agent_error(
            trace,
            "ActionModelAgent did not receive a final action within "
            f"{self.max_steps} steps.",
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
        "- Minimize steps. Prefer at most one read and one write before final.",
        "- After one useful write, prefer a final action unless another "
        "step is required.",
        f"- You have at most {max_steps} total steps.",
        f"- This is step {step_number} of {max_steps}.",
    ]

    if task.expected_artifacts:
        lines.extend(
            [
                f"- Likely relevant files: {', '.join(task.expected_artifacts)}.",
            ]
        )

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


def _extract_json_object_payload(response: str) -> dict[str, object]:
    """Extract the first JSON object from a model response.

    Args:
        response: Raw model response.

    Returns:
        dict[str, object]: Parsed JSON object payload.

    Raises:
        ValueError: If no JSON object can be decoded.
    """
    normalized_response = validate_non_empty_text(response)
    candidates = [normalized_response]

    fenced_blocks = re.findall(
        r"```(?:json)?\s*(.*?)```",
        normalized_response,
        flags=re.IGNORECASE | re.DOTALL,
    )
    candidates.extend(block.strip() for block in fenced_blocks if block.strip())

    decoder = json.JSONDecoder()
    for candidate in candidates:
        for index, char in enumerate(candidate):
            if char != "{":
                continue

            try:
                payload, _ = decoder.raw_decode(candidate, idx=index)
            except json.JSONDecodeError:
                continue

            if isinstance(payload, dict):
                return payload

    raise ValueError("Model response was not valid JSON.")


def _extract_relaxed_action_payload(response: str) -> dict[str, object]:
    """Extract a relaxed action payload from near-JSON model text.

    Args:
        response: Raw model response.

    Returns:
        dict[str, object]: Parsed action payload.

    Raises:
        ValueError: If the response does not match a supported relaxed shape.
    """
    patterns = (
        (
            _READ_ACTION,
            re.compile(
                r'\{"action":"read_file","path":"(?P<path>[^"]+)"\}',
                flags=re.DOTALL,
            ),
        ),
        (
            _WRITE_ACTION,
            re.compile(
                r'\{"action":"write_file","path":"(?P<path>[^"]+)",'
                r'"content":"(?P<content>.*)"\}',
                flags=re.DOTALL,
            ),
        ),
        (
            _FINAL_ACTION,
            re.compile(
                r'\{"action":"final","text":"(?P<text>.*)"\}',
                flags=re.DOTALL,
            ),
        ),
    )

    for action_name, pattern in patterns:
        match = pattern.search(response)
        if match is None:
            continue

        payload: dict[str, object] = {"action": action_name}
        for field_name, field_value in match.groupdict().items():
            if field_value is None:
                continue
            payload[field_name] = field_value
        return payload

    raise ValueError("Model response was not valid JSON.")


def _raise_action_model_agent_error(
    trace: RunTrace,
    message: str,
    *,
    cause: Exception | None = None,
) -> NoReturn:
    """Attach a final-output failure message and raise a trace-carrying error.

    Args:
        trace: Trace accumulated before the failure.
        message: Failure message to store and raise.
        cause: Optional underlying cause.

    Raises:
        ActionModelAgentError: Always raised with the trace attached.
    """
    if trace.final_output is None:
        trace.set_final_output(f"Action model agent failed: {message}")

    error = ActionModelAgentError(message, trace)
    if cause is not None:
        raise error from cause

    raise error
