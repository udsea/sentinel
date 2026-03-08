.PHONY: fmt lint typecheck test check

fmt:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

test:
	uv run pytest

check: fmt lint typecheck test
