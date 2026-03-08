import json
from pathlib import Path

from sentinel.agents import BenignScriptedAgent, CheatingScriptedAgent, ModelAgent
from sentinel.agents.base import BaseAgent
from sentinel.agents.providers import OpenAICompatibleTextClient
from sentinel.experiments.schema import (
    AgentSpec,
    ExperimentSpec,
    GraderSpec,
    MonitorSpec,
)
from sentinel.grading import FileContainsGrader, FileExistsGrader, PytestGrader
from sentinel.grading.base import BaseGrader
from sentinel.monitors import (
    ContentRiskMonitor,
    KeywordRiskMonitor,
    PathRiskMonitor,
    WritePolicyMonitor,
)
from sentinel.monitors.base import BaseMonitor
from sentinel.reporting import save_batch_results
from sentinel.runner import run_tasks
from sentinel.tasks.loader import load_task_specs


def build_agent_from_spec(spec: AgentSpec) -> BaseAgent:
    """Build an agent instance from experiment config.

    Args:
        spec: Agent configuration.

    Returns:
        BaseAgent: Configured agent instance.

    Raises:
        ValueError: If the config cannot be mapped to a supported agent.
    """
    if spec.kind == "benign_scripted":
        return BenignScriptedAgent()

    if spec.kind == "cheating_scripted":
        return CheatingScriptedAgent()

    if spec.kind != "model":
        raise ValueError(f"Unsupported agent kind: {spec.kind}")

    if spec.model is None:
        raise ValueError("Model agents require a model name.")

    provider = "openai_compatible" if spec.provider is None else spec.provider
    if provider == "openai_compatible":
        if spec.base_url is None:
            raise ValueError("OpenAI-compatible model agents require a base_url.")
        client = OpenAICompatibleTextClient.from_env(
            model=spec.model,
            base_url=spec.base_url,
        )
    elif provider == "openrouter":
        client = OpenAICompatibleTextClient.for_openrouter_from_env(model=spec.model)
    else:
        raise ValueError(f"Unsupported model provider: {provider}")

    return ModelAgent(client=client)


def build_graders_from_specs(specs: list[GraderSpec]) -> list[BaseGrader]:
    """Build grader instances from experiment config.

    Args:
        specs: Grader configurations.

    Returns:
        list[BaseGrader]: Configured graders.

    Raises:
        ValueError: If a grader kind is unsupported or missing required fields.
    """
    graders: list[BaseGrader] = []

    for spec in specs:
        if spec.kind == "file_exists":
            if spec.relative_path is None:
                raise ValueError("file_exists graders require a relative_path.")
            graders.append(FileExistsGrader(spec.relative_path))
            continue

        if spec.kind == "file_contains":
            if spec.relative_path is None or spec.needle is None:
                raise ValueError(
                    "file_contains graders require relative_path and needle."
                )
            graders.append(FileContainsGrader(spec.relative_path, spec.needle))
            continue

        if spec.kind == "pytest":
            relative_path = "." if spec.relative_path is None else spec.relative_path
            graders.append(
                PytestGrader(
                    relative_path=relative_path,
                    pytest_args=list(spec.pytest_args),
                )
            )
            continue

        raise ValueError(f"Unsupported grader kind: {spec.kind}")

    return graders


def build_monitors_from_specs(specs: list[MonitorSpec]) -> list[BaseMonitor]:
    """Build monitor instances from experiment config.

    Args:
        specs: Monitor configurations.

    Returns:
        list[BaseMonitor]: Configured monitors.

    Raises:
        ValueError: If a monitor kind is unsupported.
    """
    monitors: list[BaseMonitor] = []

    for spec in specs:
        if spec.kind == "path_risk":
            monitors.append(PathRiskMonitor())
            continue

        if spec.kind == "keyword_risk":
            monitors.append(KeywordRiskMonitor())
            continue

        if spec.kind == "content_risk":
            monitors.append(ContentRiskMonitor())
            continue

        if spec.kind == "write_policy":
            monitors.append(
                WritePolicyMonitor(protected_prefixes=list(spec.protected_prefixes))
            )
            continue

        raise ValueError(f"Unsupported monitor kind: {spec.kind}")

    return monitors


def run_experiment(spec: ExperimentSpec) -> Path:
    """Run an experiment config and persist the artifact bundle.

    Args:
        spec: Experiment specification to execute.

    Returns:
        Path: Output directory containing the experiment artifacts.
    """
    task_paths: list[str | Path] = list(spec.tasks)
    tasks = load_task_specs(task_paths)
    agent = build_agent_from_spec(spec.agent)
    graders = build_graders_from_specs(spec.graders)
    monitors = build_monitors_from_specs(spec.monitors)
    results = run_tasks(
        tasks=tasks,
        agent=agent,
        graders=graders,
        monitors=monitors,
    )

    output_dir = save_batch_results(results, spec.output_dir)
    _write_json_file(
        output_dir / "experiment_spec.json",
        spec.model_dump(mode="json"),
    )
    return output_dir


def _write_json_file(path: Path, payload: dict[str, object]) -> Path:
    """Write a JSON payload to disk.

    Args:
        path: Output file path.
        payload: JSON-safe payload to write.

    Returns:
        Path: Written file path.
    """
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
