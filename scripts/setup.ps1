# Mise en place complète du poste pour le TP1 (Windows PowerShell).
# Usage : powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Le .venv est PARTAGÉ : il vit dans le dossier de travail, à côté du dépôt (..\.venv),
# et sert aussi aux copies Agent_support_info_TPn.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$Venv = Join-Path (Resolve-Path "..") ".venv"

Write-Host "1/4 Vérification de Python"
py -3.11 --version

Write-Host "2/4 Environnement virtuel partagé : $Venv"
if (-not (Test-Path $Venv)) { py -3.11 -m venv $Venv }
& (Join-Path $Venv "Scripts\Activate.ps1")

Write-Host "3/4 Installation des dépendances"
python -m pip install --upgrade pip
pip install -r requirements.txt
pip freeze | Out-File -Encoding utf8 requirements.lock

Write-Host "4/4 Diagnostic"
python scripts\check_setup.py
