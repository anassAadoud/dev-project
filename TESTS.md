# Démarche à suivre pour le test

Ce dépôt se vérifie de deux façons, qui contrôlent les mêmes choses : `scripts/check_setup.py` parle aux humains (lignes OK, ATTENTION, ERREUR) et `pytest` parle à la machine (repris par la CI).

Toutes les commandes se lancent depuis la racine du dépôt, le `.venv` partagé activé (`..\.venv\Scripts\Activate.ps1`).

## TP1 : huit contrôles, T0 à T7

### T0. La structure est là

```powershell
Get-ChildItem -Force
```

Les sept dossiers (`app`, `data`, `docs`, `models`, `scripts`, `tests`, `ui`), `.github` et `.gitignore`.

### T1. Le point de départ

```powershell
python scripts/check_setup.py
python -m pytest -q
```

Avant les fiches et sans dépôt Git : `3 failed, 31 passed, 4 skipped`. Les 3 échecs sont dans `tests/test_cadrage.py` (fiches vides) ; les 4 tests ignorés attendent un dépôt Git (3 dans `tests/test_git_history.py`, 1 dans `tests/test_environment.py`).

### T2. Les fiches de cadrage

```powershell
python -m pytest tests/test_cadrage.py -q
```

Attendu : **12 passed**. Trois fichiers `docs/cadrage/cas*.md` ; les huit rubriques obligatoires présentes ; chacune remplie (au moins 20 caractères hors consigne) ; exactement une case `- [x]` ; au moins deux critères `(a)` à `(d)` dans la justification.

### T3. Rien d'indésirable dans le dépôt

```powershell
git add -A
git status
```

Aucune ligne `.venv/`, `.env` ni `.joblib`. Avec un seul auteur, pytest affiche `37 passed, 1 failed` : l'échec est `test_each_member_has_committed`.

### T4. Le diagnostic

```powershell
python scripts/check_setup.py
```

Cinq blocs (Python, Paquets, Structure, Git, Fiches), puis `N erreur(s), M avertissement(s)`. Le bloc Python indique si le venv actif est le venv partagé (`..\.venv`) ou un venv du dépôt (clone frais, CI) ; les deux sont acceptés.

### T5. Les deux membres ont commité

```powershell
git shortlog -sn --all
python -m pytest tests/test_git_history.py -q
```

Attendu : deux noms distincts, puis **3 passed**.

### T6. Tout, comme la CI

Attendu : **38 passed** (23 + 12 + 3), et `0 erreur(s), 0 avertissement(s)` au diagnostic ; l'onglet Actions vert.

### T7. Le clone frais

```bash
bash scripts/verif_clone.sh https://github.com/<compte-A>/Agent_support_info.git
```

Le clone frais crée son propre `.venv`, dans le clone : le diagnostic l'accepte. Attendu : **0 erreur(s)** et **38 passed**, sans intervention.

## Les états de référence du TP1

| État | check_setup.py | pytest |
| --- | --- | --- |
| Fichiers écrits, pas de dépôt Git, fiches vides | 1 erreur | 3 failed, 31 passed, 4 skipped |
| Dépôt initialisé, un seul auteur, fiches remplies | 0 erreur, 1 avertissement | 37 passed, 1 failed |
| Fin du TP : fiches remplies, deux auteurs | 0 erreur, 0 avertissement | 38 passed |

En cas d'échec, `DEPANNAGE.md` liste les messages et leur correction.
