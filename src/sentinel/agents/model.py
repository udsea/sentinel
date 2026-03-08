from pathlib import Path
from typing import Protocol

from sentinel.agents.base import BaseAgent
from sentinel.schemas.task import TaskSpec
from sentinel.traces import RunTrace
from sentinel.traces.events import validate_non_empty_text


class BaseTextModelClient(Protocol):
    """Minimal text-generation client boundary for model-facing agents."""

    @property
    def name(self) -> str:
        """Return the client name."""
        ...

    def generate(self, prompt: str) -> str:
        """Generate a text response from a prompt."""
        ...


def build_agent_prompt(task: TaskSpec) -> str:
    """Build the visible agent prompt for a task.

    Args:
        task: Task specification to render.

    Returns:
        str: Deterministic visible prompt text.
    """
    lines = [
        f"Goal: {task.goal}",
        "",
        "Instructions:",
        *[f"- {instruction}" for instruction in task.visible_instructions],
    ]
    return validate_non_empty_text("\n".join(lines))


class ModelAgent(BaseAgent):
    """Prompt-only agent that delegates visible-task text generation to a client."""

    def __init__(
        self,
        client: BaseTextModelClient,
        name: str | None = None,
    ) -> None:
        """Initialize the model-facing agent.

        Args:
            client: Text-generation client to call.
            name: Optional explicit agent name.
        """
        self.client = client
        self._name = name

    @property
    def name(self) -> str:
        """Return the configured or derived agent name."""
        if self._name is not None:
            return self._name

        return f"model_agent:{self.client.name}"

    def run(self, task: TaskSpec, workspace: Path) -> RunTrace:
        """Run the prompt-only model agent for a task.

        Args:
            task: Task specification to render for the model client.
            workspace: Workspace directory for trace context.

        Returns:
            RunTrace: Trace containing only the final generated output.
        """
        trace = RunTrace(task_id=task.id, workspace=str(workspace))
        prompt = build_agent_prompt(task)
        response = self.client.generate(prompt)
        trace.set_final_output(response)
        return trace
