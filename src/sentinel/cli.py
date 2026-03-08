from enum import StrEnum
from pathlib import Path
from typing import Annotated, cast

import typer

from sentinel import __version__
from sentinel.agents import BenignScriptedAgent, CheatingScriptedAgent
from sentinel.agents.base import BaseAgent
from sentinel.experiments import load_experiment_spec, run_experiment
from sentinel.grading import PytestGrader
from sentinel.grading.base import BaseGrader
from sentinel.monitors import (
    ContentRiskMonitor,
    KeywordRiskMonitor,
    PathRiskMonitor,
    SourceShortcutMonitor,
    WritePolicyMonitor,
)
from sentinel.monitors.base import BaseMonitor
from sentinel.reporting import (
    save_batch_results,
    save_run_result_json,
    summarize_run_result,
)
from sentinel.runner import run_task, run_tasks, summarize_batch
from sentinel.tasks.loader import load_task_spec, load_task_specs


class AgentChoice(StrEnum):
    """Supported scripted agents for the CLI."""

    BENIGN = "benign"
    CHEATING = "cheating"


# Initialize the Typer app
app = typer.Typer(
    name="sentinel",
    help="Inspect-based evaluation framework for coding agents.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Display the current version of Sentinel."""
    typer.echo(f"sentinel version: {__version__}")


@app.command("run-task")
def run_task_command(
    task_path: Annotated[str, typer.Argument(help="Path to a task YAML file.")],
    agent: Annotated[
        AgentChoice,
        typer.Option("--agent", help="Agent to run."),
    ] = AgentChoice.BENIGN,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Optional JSON output path."),
    ] = None,
) -> None:
    """Run a single task and print a short summary."""
    task = load_task_spec(task_path)
    result = run_task(
        task=task,
        agent=_resolve_agent(agent),
        graders=_default_graders(),
        monitors=_default_monitors(),
    )

    typer.echo(summarize_run_result(result))

    if output is not None:
        written_path = save_run_result_json(result, output)
        typer.echo(f"Saved JSON: {written_path}")


@app.command("run-batch")
def run_batch_command(
    task_paths: Annotated[
        list[str],
        typer.Argument(help="One or more task YAML paths."),
    ],
    agent: Annotated[
        AgentChoice,
        typer.Option("--agent", help="Agent to run."),
    ] = AgentChoice.BENIGN,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Optional directory for batch artifacts."),
    ] = None,
) -> None:
    """Run multiple tasks and print a compact batch summary."""
    tasks = load_task_specs([Path(task_path) for task_path in task_paths])
    results = run_tasks(
        tasks=tasks,
        agent=_resolve_agent(agent),
        graders=_default_graders(),
        monitors=_default_monitors(),
    )
    summary = summarize_batch(results)

    typer.echo(_format_batch_summary(summary))

    if output_dir is not None:
        written_dir = save_batch_results(results, output_dir)
        typer.echo(f"Saved batch artifacts to: {written_dir}")


@app.command("run-experiment")
def run_experiment_command(
    experiment_path: Annotated[
        str,
        typer.Argument(help="Path to an experiment YAML file."),
    ],
) -> None:
    """Run an experiment config and write its artifact bundle."""
    spec = load_experiment_spec(experiment_path)
    output_dir = run_experiment(spec)
    typer.echo(f"Experiment artifacts written to: {output_dir}")


@app.callback()
def main() -> None:
    """Sentinel CLI entry point."""
    pass


def _resolve_agent(name: AgentChoice) -> BaseAgent:
    """Resolve a CLI agent choice to an agent instance.

    Args:
        name: CLI agent choice.

    Returns:
        BaseAgent: Scripted agent instance.
    """
    if name is AgentChoice.BENIGN:
        return BenignScriptedAgent()
    if name is AgentChoice.CHEATING:
        return CheatingScriptedAgent()

    raise ValueError(f"Unsupported agent: {name}")


def _default_graders() -> list[BaseGrader]:
    """Return the default grader set for the CLI.

    Returns:
        list[BaseGrader]: Default graders.
    """
    return [PytestGrader(relative_path="tests", pytest_args=["-q"])]


def _default_monitors() -> list[BaseMonitor]:
    """Return the default monitor set for the CLI.

    Returns:
        list[BaseMonitor]: Default monitors.
    """
    return [
        PathRiskMonitor(),
        KeywordRiskMonitor(),
        ContentRiskMonitor(),
        SourceShortcutMonitor(),
        WritePolicyMonitor(protected_prefixes=["tests/"]),
    ]


def _format_batch_summary(summary: dict[str, object]) -> str:
    """Format a compact batch summary for terminal output.

    Args:
        summary: Aggregate batch summary.

    Returns:
        str: Human-readable batch summary text.
    """
    total_runs = cast(int, summary["total_runs"])
    passed_runs = cast(int, summary["passed_runs"])
    flagged_runs = cast(int, summary["flagged_runs"])
    failed_runs = cast(int, summary["failed_runs"])
    pass_rate = cast(float, summary["pass_rate"])
    flag_rate = cast(float, summary["flag_rate"])

    lines = [
        f"Total runs: {total_runs}",
        f"Passed runs: {passed_runs}",
        f"Flagged runs: {flagged_runs}",
        f"Failed runs: {failed_runs}",
        f"Pass rate: {pass_rate:.2f}",
        f"Flag rate: {flag_rate:.2f}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    app()
