#!/usr/bin/env bash

set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "ERROR: OPENROUTER_API_KEY is not set."
  exit 1
fi

echo "Running OpenRouter action benign smoke experiment..."
uv run sentinel run-experiment tests/fixtures/experiments/openrouter_action_benign_smoke.yaml

echo "Running OpenRouter action cheating smoke experiment..."
uv run sentinel run-experiment tests/fixtures/experiments/openrouter_action_cheating_smoke.yaml

echo
echo "Done."
echo "Artifacts:"
echo "  outputs/openrouter_action_benign_smoke"
echo "  outputs/openrouter_action_cheating_smoke"
