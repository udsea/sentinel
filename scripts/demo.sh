#!/usr/bin/env bash

set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

mkdir -p outputs/demo

uv run sentinel run-task \
  tests/fixtures/tasks/fix_pagination_v1.yaml \
  --agent benign \
  --output outputs/demo/benign_run.json

uv run sentinel run-batch \
  tests/fixtures/tasks/hide_failing_test_v1.yaml \
  tests/fixtures/tasks/shortcut_completion_checks_v1.yaml \
  --agent cheating \
  --output-dir outputs/demo/demo_batch

echo "Demo artifacts written to outputs/demo/"
