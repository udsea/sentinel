from sentinel.agents.model import build_agent_prompt
from sentinel.inspect_integration.sample import InspectSample
from sentinel.schemas.task import TaskSpec


def task_spec_to_inspect_sample(task: TaskSpec) -> InspectSample:
    """Convert a Sentinel task spec into an Inspect-aligned sample.

    Args:
        task: Task specification to convert.

    Returns:
        InspectSample: Inspect-facing sample payload.
    """
    metadata: dict[str, object] = {
        "track": task.track,
        "difficulty": task.difficulty,
        "goal": task.goal,
        "risk_tags": list(task.risk_tags),
        "hidden_constraints": list(task.hidden_constraints),
        "temptations": list(task.temptations),
        "expected_artifacts": list(task.expected_artifacts),
        "task_metadata": {key: value for key, value in task.metadata.items()},
    }

    return InspectSample(
        id=task.id,
        input=build_agent_prompt(task),
        metadata=metadata,
        sandbox_fixture=task.repo_fixture,
    )
