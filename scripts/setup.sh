#!/usr/bin/env bash
# Mise en place complète du poste pour le TP1 (Linux / macOS / Git Bash).
# Usage : bash scripts/setup.sh
# Le .venv est PARTAGÉ : il vit dans le dossier de travail, à côté du dépôt (../.venv).
set -euo pipefail
cd "$(dirname "$0")/.."
VENV="../.venv"

echo "1/4 Vérification de Python 3.11"
PY=$(command -v python3.11 || command -v python3 || command -v python)
"$PY" --version

echo "2/4 Environnement virtuel partagé : $VENV"
[ -d "$VENV" ] || "$PY" -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate" 2>/dev/null || source "$VENV/Scripts/activate"

echo "3/4 Installation des dépendances"
python -m pip install --upgrade pip
pip install -r requirements.txt
pip freeze > requirements.lock

echo "4/4 Diagnostic"
python scripts/check_setup.py
