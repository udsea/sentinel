# Sentinel

Sentinel is a lightweight evaluation harness for coding agents, with task specs, isolated workspaces, scripted agents, traces, graders, monitors, runners, artifact export, and Inspect-aligned packaging.

## Why This Exists

Sentinel is for evaluating coding-agent behavior in a controlled environment. It is designed to make oversight logic testable, keep runs reproducible, and produce concrete artifacts that another engineer can inspect later.

## Core Features

- Declarative task specs in YAML
- Isolated fixture-backed workspaces
- Deterministic scripted agents for regression testing
- Structured run traces with file reads, file writes, and final output
- Static graders for workspace state checks
- Heuristic monitors for path and output risk
- Single-task and batch runners
- JSON export for run and batch artifacts
- Inspect-aligned task packaging and packaged execution
- CLI entrypoints for basic execution

## What Sentinel Does Today

- Runs deterministic scripted agents against isolated workspace copies
- Applies static file-based graders to resulting workspace state
- Applies heuristic monitors to run traces
- Exports per-run and batch artifact bundles as JSON
- Packages Sentinel tasks into Inspect-aligned samples and task stubs

## Project Structure

```text
src/sentinel/
├── agents/
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
│   ├── repos/
│   └── tasks/
└── test_*.py
docs/
├── architecture.md
└── examples/
scripts/
└── demo.sh
```

## Quickstart

Requirements:

- Python 3.11+
- `uv`

Sample task YAMLs for local runs live in [tests/fixtures/tasks/valid_minimal.yaml](/Users/udbhav/Dev/tinkering/sentinel/tests/fixtures/tasks/valid_minimal.yaml) and [tests/fixtures/tasks/valid_full.yaml](/Users/udbhav/Dev/tinkering/sentinel/tests/fixtures/tasks/valid_full.yaml).

```bash
uv sync --dev
uv run sentinel version
uv run sentinel run-task tests/fixtures/tasks/valid_minimal.yaml --agent benign
```

One additional batch example:

```bash
uv run sentinel run-batch \
  tests/fixtures/tasks/valid_minimal.yaml \
  tests/fixtures/tasks/valid_full.yaml \
  --agent benign
```

To save a single run as JSON:

```bash
uv run sentinel run-task \
  tests/fixtures/tasks/valid_minimal.yaml \
  --agent benign \
  --output outputs/run.json
```

## Demo

Benign single-task run:

```bash
uv run sentinel run-task tests/fixtures/tasks/valid_minimal.yaml --agent benign --output outputs/benign_run.json
```

Cheating batch run:

```bash
uv run sentinel run-batch \
  tests/fixtures/tasks/valid_minimal.yaml \
  tests/fixtures/tasks/valid_full.yaml \
  --agent cheating \
  --output-dir outputs/demo_batch
```

Expected artifact tree:

```text
outputs/
├── benign_run.json
└── demo_batch/
    ├── batch_summary.json
    ├── manifest.json
    ├── fix_app_v1.json
    └── fix_app_v2.json
```

Example outputs live in [docs/examples/benign_run_summary.txt](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/benign_run_summary.txt), [docs/examples/cheating_batch_summary.txt](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/cheating_batch_summary.txt), and [docs/examples/artifact_layout.txt](/Users/udbhav/Dev/tinkering/sentinel/docs/examples/artifact_layout.txt).

## Architecture Overview

Core flow:

`Task spec -> workspace -> agent -> trace -> graders/monitors -> runner -> reporting`

The task spec selects a fixture repo, the sandbox layer materializes an isolated workspace, the agent acts in that workspace, the trace captures what happened, graders inspect resulting files, monitors inspect behavior, and reporting turns the result into artifacts. More detail is in [docs/architecture.md](/Users/udbhav/Dev/tinkering/sentinel/docs/architecture.md).

## Example Artifact Outputs

The batch reporting layer can persist a bundle like this:

```text
outputs/demo_batch/
├── batch_summary.json
├── manifest.json
├── fix_app_v1.json
└── fix_app_v2.json
```

- `batch_summary.json`: aggregate counts and rates for the batch
- `manifest.json`: task ids, agent names, passed task ids, and flagged task ids
- `<task_id>.json`: full serialized `RunResult` for each run

## Current Limitations

- Sentinel currently uses scripted agents only.
- There is no real model or API integration yet.
- Graders are intentionally simple and static.
- Monitors are heuristic and not learned.
- There is no concurrency or larger experiment orchestration layer yet.

## Roadmap

- Optional `inspect_ai` dependency integration and task registration
- Richer grading backends
- Additional monitor families
- Batch experiment configuration
- More realistic coding-task fixtures
