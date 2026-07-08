PYTHON ?= python3.12
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: venv install check check-data init-data context-registry clean-cache

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

check:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PY) -m compileall -q src scripts fetch_orthophotos_stac.py

check-data:
	PYTHONDONTWRITEBYTECODE=1 $(PY) scripts/check_data_inventory.py --strict

init-data:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PY) -m slowvaud.cli init

context-registry:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src $(PY) -m slowvaud.cli context-registry

clean-cache:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -prune -exec rm -rf {} +
