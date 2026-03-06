PHONY: help venv install download prepare split windows train eval clean coverage

PY := python
UV := uv

help:
	@echo "Targets:"
	@echo "  make install   - install deps into .venv"
	@echo "  make download  - download raw NCBI datasets"
	@echo "  make prepare   - build genomes.jsonl"
	@echo "  make split     - create genome-level splits"
	@echo "  make windows   - create LM windows"
	@echo "  make train     - train baseline model"
	@echo "  make eval      - run evaluation"
	@echo "  make clean     - remove generated artifacts"

install:
	$(UV) sync


split:
	$(PY) scripts/make_splits.py

windows:
	$(PY) scripts/make_windows.py

train:
	$(PY) -m genomebench.train --config configs/train.yaml

eval:
	$(PY) -m genomebench.eval --config configs/eval.yaml

clean:
	rm -rf data/processed results .pytest_cache

coverage:
	uv run pytest --cov=src/genomebench --cov-report=term-missing --cov-report=html

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
