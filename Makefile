# Raccourcis du TP1. Linux, macOS et Git Bash ; sous Windows, lancez les
# commandes directement ou utilisez scripts\setup.ps1.
# Le .venv est partagé : il se trouve dans le dossier parent (../.venv).

VENV ?= ../.venv
PY := $(shell [ -x $(VENV)/bin/python ] && echo $(VENV)/bin/python || echo $(VENV)/Scripts/python)

.PHONY: help setup check test test-cadrage test-env test-git verif clean

help:
	@echo "Cibles disponibles :"
	@echo "  make setup        installe le venv partagé et les dependances, puis diagnostique"
	@echo "  make check        lance le diagnostic lisible"
	@echo "  make test         lance tous les tests"
	@echo "  make test-cadrage lance les 12 tests des fiches"
	@echo "  make test-env     lance les 23 tests d'environnement"
	@echo "  make test-git     lance les 3 tests d'historique Git"
	@echo "  make verif URL=<url>  rejoue le test de l'enseignant sur un clone frais"
	@echo "  make clean        supprime les caches (garde le venv)"

setup:
	bash scripts/setup.sh

check:
	$(PY) scripts/check_setup.py

test:
	$(PY) -m pytest -q

test-cadrage:
	$(PY) -m pytest tests/test_cadrage.py -q

test-env:
	$(PY) -m pytest tests/test_environment.py -q

test-git:
	$(PY) -m pytest tests/test_git_history.py -q

verif:
	@test -n "$(URL)" || (echo "Usage : make verif URL=https://github.com/<compte-A>/Agent_support_info.git"; exit 2)
	bash scripts/verif_clone.sh $(URL)

clean:
	rm -rf .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
