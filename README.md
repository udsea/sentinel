# Sentinel

Sentinel is a lightweight evaluation harness for coding agents, with task specs, isolated workspaces, traces, graders, monitors, runners, and JSON artifact export.

## Why Sentinel Exists

Sentinel is for evaluating coding-agent behavior in a controlled environment. It is designed to make oversight logic testable, keep runs reproducible, and produce artifacts that another engineer can inspect after the run.

## Quickstart

Requirements:

- Python 3.11+
- `uv`

```bash
uv sync --dev
uv run sentinel version
uv run sentinel run-task tests/fixtures/tasks/fix_pagination_v1.yaml --agent benign
```

Sample task YAMLs live under [tests/fixtures/tasks/](/Users/udbhav/Dev/tinkering/sentinel/tests/fixtures/tasks), and the one-shot human demo lives at [scripts/demo.sh](/Users/udbhav/Dev/tinkering/sentinel/scripts/demo.sh).

## End-to-End Demo

Benign demo:

```bash
uv run sentinel run-task \
  tests/fixtures/tasks/fix_pagination_v1.yaml \
  --agent benign \
  --output outputs/demo/benign_run.json
```

Cheating demo:

```bash
uv run sentinel run-task \
  tests/fixtures/tasks/hide_failing_test_v1.yaml \
  --agent cheating \
  --output outputs/demo/cheating_run.json
```

One-shot helper:

```bash
bash scripts/demo.sh
```

Expected output tree:

```text
outputs/demo/
├── benign_run.json
└── cheating_run.json
```

What to look for:

- The benign run should show `all_graders_passed: true` and `any_monitor_flagged: false`.
- The cheating run may still pass grading, but `monitor_aggregate.any_flagged` should be `true`.
- The cheating run should list multiple flagged monitors, including path-based, keyword-based, and content-based checks.
- That contrast is intentional: Sentinel is demonstrating oversight beyond task-success alone.

Curated example outputs live in:

- [docs/examples/benign_run_summary.txt](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/benign_run_summary.txt)
- [docs/examples/cheating_run_summary.txt](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/cheating_run_summary.txt)
- [docs/examples/demo_notes.md](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/demo_notes.md)

## Real-Model Smoke Validation

Sentinel also includes small OpenRouter-backed smoke experiment configs for validating the model-agent path end to end.

Setup:

```bash
export OPENROUTER_API_KEY=your_api_key_here
bash scripts/demo_openrouter.sh
```

Bounded action smoke:

```bash
export OPENROUTER_API_KEY=your_api_key_here
bash scripts/demo_openrouter_action.sh
```

What success looks like:

- `outputs/openrouter_benign_smoke` and `outputs/openrouter_cheating_smoke` are created
- `outputs/openrouter_action_benign_smoke` and `outputs/openrouter_action_cheating_smoke` are created
- each output dir contains `batch_summary.json`, `manifest.json`, `experiment_spec.json`, and per-task run JSON files
- the runs complete through the native experiment pipeline without manual wiring

What this validates:

- provider-backed model-agent construction
- bounded read/write/final action execution for the action-model path
- executable grading through `PytestGrader`
- monitor execution over real-model final outputs
- monitor execution over real-model file writes for the action-model path
- artifact export for benign and cheating-style task sets

What this does not claim:

- this is a proof-of-life smoke path, not a benchmark
- it is not broad empirical validation across many models
- cheating-style monitor outcomes may vary with actual model choices and prompts

## Core Architecture Flow

`Task spec -> workspace -> agent -> trace -> graders/monitors -> runner -> reporting`

The task spec selects a fixture repo, the sandbox layer materializes an isolated workspace, the agent acts inside it, the trace records what happened, graders inspect resulting workspace state, monitors inspect behavioral signals, and reporting writes inspectable artifacts. More detail is in [docs/architecture.md](/Users/udbhav/Dev/tinkering/sentinel/docs/architecture.md).

## Project Structure

```text
src/sentinel/
├── agents/
│   └── providers/
├── experiments/
├── grading/
├── inspect_integration/
├── monitors/
├── reporting/
├── runner/
├── sandbox/
├── schemas/
├── tasks/
└── traces/
tests/
├── fixtures/
│   ├── experiments/
│   ├── repos/
│   └── tasks/
└── test_*.py
docs/
├── architecture.md
└── examples/
scripts/
└── demo.sh
```

## Artifact Outputs

Each single-run JSON artifact includes the task id, workspace path, run trace, grader results, raw monitor results, and the monitor aggregate. The canonical demo writes:

```text
outputs/demo/
├── benign_run.json
└── cheating_run.json
```

Reference layouts live in:

- [docs/examples/benign_artifact_layout.txt](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/benign_artifact_layout.txt)
- [docs/examples/cheating_artifact_layout.txt](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/cheating_artifact_layout.txt)

### What Sentinel Does Today

- Runs deterministic scripted agents against isolated workspace copies
- Includes a bounded action-taking model agent with `read_file`, `write_file`, and `final`
- Applies static and pytest-backed graders to workspace state
- Applies heuristic path, output, content, and write-policy monitors to run traces
- Exports per-run and batch artifact bundles as JSON
- Packages Sentinel tasks into Inspect-aligned samples and task stubs

## Current Limitations

- The strongest end-to-end demos currently use scripted agents, not tool-using model runtimes.
- The action-model path is intentionally narrow: `read_file`, `write_file`, and `final` only, with a max of 3 steps.
- Monitors are heuristic and intentionally simple.
- There is no concurrency or large experiment scheduler yet.
- Workspace paths captured in artifacts refer to ephemeral temp directories from the original run.

## Roadmap

- Optional `inspect_ai` dependency integration and task registration
- Richer grading backends
- Additional monitor families
- More realistic model/action agent paths
- Larger experiment orchestration and comparison workflows
