# Dépannage

Cherchez votre message dans la première colonne.

| Message ou symptôme | Cause | Correction |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pandas'` | venv partagé non activé | `..\.venv\Scripts\Activate.ps1` depuis le dépôt ; `where python` doit afficher `...\project\.venv\Scripts\python.exe` |
| `ERREUR aucun environnement virtuel actif` au diagnostic | idem | idem |
| `ATTENTION environnement virtuel actif, mais ni ..\.venv ni .venv` | un autre venv est actif (par exemple celui de `sentiment-app`) | `deactivate`, puis activer `..\.venv` |
| `test_virtualenv_active` échoue | pytest lancé hors du venv | activer le venv, ou `..\.venv\Scripts\python.exe -m pytest` |
| `No matching distribution found for scikit-learn==1.5.*` | Python 3.12 ou plus | recréer le venv partagé avec `py -3.11 -m venv ..\.venv` |
| `Activate.ps1 cannot be loaded` | politique PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `Please tell me who you are` au commit | identité Git non configurée | `git config --global user.name` et `user.email` |
| `1 auteur(s) de commits, 2 attendus` | le membre B n'a pas encore commité | le membre B clone, ajoute sa ligne au README, commite et pousse |
| `rubriques vides ou trop courtes : ...` | une rubrique de fiche est vide | remplir la rubrique nommée |
| `cocher exactement une approche` | zéro ou deux cases `- [x]` | une seule approche par fiche |
| `la justification doit citer au moins deux critères` | les lettres `(a)` à `(d)` manquent | les écrire telles quelles |
| `git` échoue sur un fichier verrouillé (`Permission denied`, `unable to unlink`) | le dossier est dans OneDrive, la synchronisation tient le fichier | attendre la fin de la synchronisation, réessayer une fois, le noter dans le journal |
| `robocopy` renvoie un code de 1 à 7 | copie réussie (codes de robocopy) | rien à faire ; 8 et plus signalent un échec |

## Le .venv partagé

Un seul `.venv` (Python 3.11) vit dans le dossier de travail, à côté de `Agent_support_info/` et des copies `Agent_support_info_TPn`. Les scripts (`scripts/setup.ps1`, `scripts/check_setup.py`) et les tests le cherchent là. Un clone frais ailleurs peut avoir son propre `.venv` dans le dépôt : il est accepté aussi, et `.gitignore` l'exclut dans les deux cas.

## Si rien de tout cela ne marche

Noter trois éléments : la commande exacte, le message complet, et la sortie de `python scripts/check_setup.py`.
