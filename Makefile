PYTHON ?= python3.12
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: venv install check init-data manifest context-registry clean-cache

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

check:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PY) -m compileall -q src scripts fetch_orthophotos_wmts.py

init-data:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PY) -m slowvaud.cli init

manifest:
	PYTHONDONTWRITEBYTECODE=1 $(PY) fetch_orthophotos_wmts.py --profiles preview --max-tiles 5 --dry-run

context-registry:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PY) -m slowvaud.cli context-registry

clean-cache:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -prune -exec rm -rf {} +
