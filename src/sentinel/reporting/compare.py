from sentinel.runner.result import RunResult


def compare_run_results(
    baseline: RunResult,
    candidate: RunResult,
) -> dict[str, object]:
    """Compare two single-run results.

    Args:
        baseline: Baseline run result.
        candidate: Candidate run result.

    Returns:
        dict[str, object]: JSON-safe comparison summary.
    """
    same_task = baseline.task_id == candidate.task_id
    baseline_output = (
        None
        if baseline.trace.final_output is None
        else baseline.trace.final_output.text
    )
    candidate_output = (
        None
        if candidate.trace.final_output is None
        else candidate.trace.final_output.text
    )

    return {
        "task_id": (
            baseline.task_id
            if same_task
            else f"{baseline.task_id} -> {candidate.task_id}"
        ),
        "baseline_task_id": baseline.task_id,
        "candidate_task_id": candidate.task_id,
        "same_task": same_task,
        "agent_changed": baseline.agent_name != candidate.agent_name,
        "grader_pass_changed": (
            baseline.all_graders_passed != candidate.all_graders_passed
        ),
        "monitor_flag_changed": (
            baseline.any_monitor_flagged != candidate.any_monitor_flagged
        ),
        "baseline_all_graders_passed": baseline.all_graders_passed,
        "candidate_all_graders_passed": candidate.all_graders_passed,
        "baseline_any_monitor_flagged": baseline.any_monitor_flagged,
        "candidate_any_monitor_flagged": candidate.any_monitor_flagged,
        "baseline_flagged_monitors": list(
            baseline.monitor_aggregate.flagged_monitor_names
        ),
        "candidate_flagged_monitors": list(
            candidate.monitor_aggregate.flagged_monitor_names
        ),
        "baseline_read_count": len(baseline.trace.file_reads),
        "candidate_read_count": len(candidate.trace.file_reads),
        "baseline_write_count": len(baseline.trace.file_writes),
        "candidate_write_count": len(candidate.trace.file_writes),
        "final_output_changed": baseline_output != candidate_output,
    }


def compare_batches(
    baseline: list[RunResult],
    candidate: list[RunResult],
) -> dict[str, object]:
    """Compare two batches of run results keyed by task id.

    Args:
        baseline: Baseline batch results.
        candidate: Candidate batch results.

    Returns:
        dict[str, object]: JSON-safe batch comparison summary.
    """
    baseline_index = _index_results_by_task_id(baseline)
    candidate_index = _index_results_by_task_id(candidate)

    baseline_task_ids = set(baseline_index)
    candidate_task_ids = set(candidate_index)
    shared_task_ids = sorted(baseline_task_ids & candidate_task_ids)

    improved_task_ids: list[str] = []
    regressed_task_ids: list[str] = []
    newly_flagged_task_ids: list[str] = []
    no_longer_flagged_task_ids: list[str] = []

    for task_id in shared_task_ids:
        baseline_result = baseline_index[task_id]
        candidate_result = candidate_index[task_id]

        if (
            not baseline_result.all_graders_passed
            and candidate_result.all_graders_passed
        ):
            improved_task_ids.append(task_id)

        if (
            baseline_result.all_graders_passed
            and not candidate_result.all_graders_passed
        ):
            regressed_task_ids.append(task_id)

        if (
            not baseline_result.any_monitor_flagged
            and candidate_result.any_monitor_flagged
        ):
            newly_flagged_task_ids.append(task_id)

        if (
            baseline_result.any_monitor_flagged
            and not candidate_result.any_monitor_flagged
        ):
            no_longer_flagged_task_ids.append(task_id)

    return {
        "baseline_total_runs": len(baseline),
        "candidate_total_runs": len(candidate),
        "shared_task_ids": shared_task_ids,
        "baseline_only_task_ids": sorted(baseline_task_ids - candidate_task_ids),
        "candidate_only_task_ids": sorted(candidate_task_ids - baseline_task_ids),
        "improved_task_ids": improved_task_ids,
        "regressed_task_ids": regressed_task_ids,
        "newly_flagged_task_ids": newly_flagged_task_ids,
        "no_longer_flagged_task_ids": no_longer_flagged_task_ids,
    }


def _index_results_by_task_id(results: list[RunResult]) -> dict[str, RunResult]:
    """Index run results by task id.

    Args:
        results: Run results to index.

    Returns:
        dict[str, RunResult]: Results keyed by task id.

    Raises:
        ValueError: If duplicate task ids are encountered.
    """
    indexed_results: dict[str, RunResult] = {}

    for result in results:
        if result.task_id in indexed_results:
            raise ValueError(f"Duplicate task_id in batch comparison: {result.task_id}")
        indexed_results[result.task_id] = result

    return indexed_results
