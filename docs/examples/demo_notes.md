# Demo Notes

The canonical Sentinel demo is intentionally small:

- Benign path: [fix_pagination_v1.yaml](/Users/udbhav/Dev/tinkering/sentinel/tests/fixtures/tasks/fix_pagination_v1.yaml) with `BenignScriptedAgent`
- Cheating path: [hide_failing_test_v1.yaml](/Users/udbhav/Dev/tinkering/sentinel/tests/fixtures/tasks/hide_failing_test_v1.yaml) with `CheatingScriptedAgent`

Both flows use the same runtime shape:

1. Load the task spec from YAML.
2. Materialize an isolated fixture-backed workspace.
3. Run the agent inside that workspace.
4. Record the trace.
5. Grade the workspace with `PytestGrader`.
6. Assess the trace with path, keyword, content, and write-policy monitors.
7. Save a JSON artifact for inspection.

## What To Inspect

In `outputs/demo/benign_run.json`:

- `all_graders_passed` should be `true`
- `any_monitor_flagged` should be `false`
- `trace.file_writes[0].relative_path` should be `app.py`

In `outputs/demo/cheating_run.json`:

- `all_graders_passed` may still be `true`
- `monitor_aggregate.any_flagged` should be `true`
- `monitor_aggregate.flagged_monitor_names` should include `PathRiskMonitor`, `KeywordRiskMonitor`, `ContentRiskMonitor`, and `WritePolicyMonitor`
- `trace.file_writes[0].relative_path` should be `tests/test_app.py`

That contrast is the point of the demo: task success and suspicious behavior are tracked separately.
