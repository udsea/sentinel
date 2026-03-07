# Sentinel

Inspect-based evaluation framework for coding agents.

Sentinel is a developer-first framework for building, running, and scaling evaluations for agentic coding systems with clean engineering practices, reproducibility, and fast iteration in mind.

## Features

- Inspect-based eval workflow for coding agents
- Clean CLI powered by Typer
- `uv`-based dependency and environment management
- Testing with `pytest`
- Linting with `ruff`
- Static typing with `mypy`
- Simple developer workflow through `make`

## Requirements

- Python 3.11+
- `uv`

## Setup / Install

```bash
git clone https://github.com/udsea/sentinel.git
cd sentinel
uv sync --dev
uv pip install -e .
