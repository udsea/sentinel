# Sentinel

Sentinel is a lightweight evaluation harness for coding agents, with task specs, isolated workspaces, deterministic and model-backed agents, executable grading, behavioral monitors, experiment configs, and JSON artifact export.

## Why Sentinel Exists

Sentinel is for evaluating coding-agent behavior in a controlled environment. It is built to make oversight logic testable, keep runs reproducible, and leave behind artifacts that another engineer can inspect after the run.

Sentinel is designed for cases where a coding agent can appear successful while still behaving suspiciously, for example by overfitting to tests, editing protected paths, or taking shortcut actions that grading alone would miss.

## Quickstart

Requirements:

- Python 3.11+
- `uv`

```bash
uv sync --dev
uv run sentinel version
uv run sentinel run-task tests/fixtures/tasks/fix_pagination_v1.yaml --agent benign
uv run sentinel run-experiment tests/fixtures/experiments/benign_demo.yaml
```

Useful entry points:

- Task fixtures: [`tests/fixtures/tasks/`](tests/fixtures/tasks/)
- Experiment configs: [`tests/fixtures/experiments/`](tests/fixtures/experiments/)
- Human demo scripts: [`scripts/`](scripts/)

Best place to start: run `bash scripts/demo.sh` for the scripted path, then `bash scripts/demo_openrouter_action.sh` for the real-model smoke path.

## End-to-End Demo

Scripted benign demo:

```bash
uv run sentinel run-task \
  tests/fixtures/tasks/fix_pagination_v1.yaml \
  --agent benign \
  --output outputs/demo/benign_run.json
```

Scripted cheating demo:

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
- The cheating run should list multiple flagged monitors, including path-based, keyword-based, content-based, and policy-based checks.
- That contrast is intentional: Sentinel tracks task success and suspicious behavior separately.

Curated scripted-demo examples:

- [`docs/examples/benign_run_summary.txt`](docs/examples/benign_run_summary.txt)
- [`docs/examples/cheating_run_summary.txt`](docs/examples/cheating_run_summary.txt)
- [`docs/examples/demo_notes.md`](docs/examples/demo_notes.md)

## Real-Model Smoke Validation

Sentinel also includes OpenRouter-backed smoke configs for validating the model-agent path end to end.

Prompt-only smoke:

```bash
export OPENROUTER_API_KEY=your_api_key_here
bash scripts/demo_openrouter.sh
```

Bounded action smoke:

```bash
export OPENROUTER_API_KEY=your_api_key_here
bash scripts/demo_openrouter_action.sh
```

What this validates:

- provider-backed model-agent construction through an OpenAI-compatible client boundary
- bounded `read_file` / `write_file` / `final` action execution for the action-model path
- executable grading through `PytestGrader`
- monitor execution over real-model outputs and file-write traces
- artifact export for benign and cheating-style task sets

### Current Live Finding

- benign runs exercise the full pipeline, including workspace creation, grading, monitor execution, and artifact export
- cheating-style runs can still pass grading while being flagged by monitors
- `SourceShortcutMonitor` catches test-informed source edits even when protected test files are not modified directly

This is a proof-of-life smoke path, not a benchmark. Model behavior varies with the selected model, prompt shape, and bounded step limit.

Curated real-model examples:

- [`docs/examples/real_model_demo/benign_summary.txt`](docs/examples/real_model_demo/benign_summary.txt)
- [`docs/examples/real_model_demo/cheating_summary.txt`](docs/examples/real_model_demo/cheating_summary.txt)
- [`docs/examples/real_model_demo/demo_note.md`](docs/examples/real_model_demo/demo_note.md)

## What Sentinel Does Today

- Runs deterministic scripted agents against isolated fixture-backed workspaces
- Runs prompt-only and bounded action-taking model agents through a provider-agnostic text client boundary
- Supports OpenAI-compatible and OpenRouter-backed model smoke paths
- Applies static file checks and executable grading with `PytestGrader`
- Applies heuristic monitors for protected-path writes, risky final-output language, suspicious written content, configurable write policy, and test-informed shortcut edits
- Runs single tasks, batches, and config-driven experiments from YAML
- Exports per-run JSON artifacts, batch summaries, manifests, and experiment specs
- Compares runs and batches to surface regressions, improvements, and monitor changes
- Packages tasks into Inspect-aligned samples, task stubs, execution results, and reporting artifacts

## Core Architecture Flow

`task spec -> workspace -> agent -> trace -> graders / monitors -> runner -> reporting`

The task spec selects a fixture repo, the sandbox layer materializes an isolated workspace, the agent acts inside it, the trace records reads, writes, and final output, graders inspect resulting workspace state, monitors inspect behavior, and reporting writes inspectable artifacts.

More detail is in [`docs/architecture.md`](docs/architecture.md).

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
├── demo.sh
├── demo_openrouter.sh
└── demo_openrouter_action.sh
```

## Artifact Outputs

Single-run artifacts include the task id, workspace path, trace, grader results, raw monitor results, and monitor aggregate.

Batch and experiment bundles include:

```text
outputs/some_run/
├── batch_summary.json
├── manifest.json
├── experiment_spec.json
├── fix_pagination_v1.json
└── hide_failing_test_v1.json
```

Reference layouts:

- [`docs/examples/benign_artifact_layout.txt`](docs/examples/benign_artifact_layout.txt)
- [`docs/examples/cheating_artifact_layout.txt`](docs/examples/cheating_artifact_layout.txt)

## Current Limitations

- The live model-agent path is intentionally narrow: text generation only for `ModelAgent`, and bounded `read_file`, `write_file`, `final` actions only for `ActionModelAgent`
- There is no general tool runtime yet: no shell execution, no planner loop, and no unrestricted file/tool interface for model agents
- Monitor logic is heuristic and intentionally simple, not learned or calibrated
- OpenRouter smoke runs are proof-of-life validations, not broad empirical benchmarks
- There is no concurrency layer, sweep engine, or large-scale experiment scheduler yet
- Workspace paths captured in artifacts refer to ephemeral temp directories from the original run

## Roadmap

- Optional `inspect_ai` dependency integration and task registration
- Richer model-action runtimes beyond the current bounded loop
- Additional monitor families and better failure analysis tooling
- More realistic coding-task fixtures and experiment sets
- Larger experiment orchestration and comparison workflows
