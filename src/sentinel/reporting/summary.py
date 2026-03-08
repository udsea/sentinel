from sentinel.runner import RunResult


def summarize_run_result(result: RunResult) -> str:
    """Return a short human-readable summary of a run result.

    Args:
        result: Run result to summarize.

    Returns:
        str: Multi-line summary text.
    """
    final_output = (
        result.trace.final_output.text
        if result.trace.final_output is not None
        else "<none>"
    )
    flagged_monitors = (
        ", ".join(result.monitor_aggregate.flagged_monitor_names)
        if result.monitor_aggregate.flagged_monitor_names
        else "<none>"
    )

    lines = [
        f"Task: {result.task_id}",
        f"Agent: {result.agent_name}",
        f"Graders passed: {_format_bool(result.all_graders_passed)}",
        f"Monitor flagged: {_format_bool(result.any_monitor_flagged)}",
        f"Flagged monitors: {flagged_monitors}",
        f"Reads: {len(result.trace.file_reads)}",
        f"Writes: {len(result.trace.file_writes)}",
        f"Final output: {final_output}",
    ]
    return "\n".join(lines)


def _format_bool(value: bool) -> str:
    """Format a boolean as `yes` or `no`.

    Args:
        value: Boolean value to format.

    Returns:
        str: Human-readable boolean string.
    """
    return "yes" if value else "no"
