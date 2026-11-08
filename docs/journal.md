# Journal de bord du binôme : Agent_support_info, TP1 à TP6

**Module** : Développement et déploiement d'applications intelligentes · **Enseignant** : A. Larhlimi · **Projet** : sujet 9, *Agent de support informatique*

|  | Membre A | Membre B |
| :---- | :---- | :---- |
| Nom | Aadoud Anass | *à compléter* |
| Compte GitHub | anass0031 | *à compléter* |

**Dépôt** : *adresse du dépôt GitHub, à compléter (voir « À faire par l'humain »)*

Ce journal est adapté de celui de `sentiment-app` : même structure (préparation, un bloc par contrôle, difficultés, répartition, bilan), contenu propre à notre projet. Le travail sur les postes est fait par le membre A avec Claude Code ; les actions qui demandent un compte, un mot de passe ou le membre B sont listées dans « À faire par l'humain ».

## Plan du projet (écrit le 8 novembre 2026, avant de commencer)

**TP1 : cadrer et préparer l'environnement.** Un `.venv` Python 3.11 partagé dans le dossier de travail, à côté du dépôt. Une structure de dépôt parallèle à `sentiment-app` (`app`, `data`, `docs`, `models`, `scripts`, `tests`, `ui`, `.github`). Les scripts `setup.ps1` et `check_setup.py` cherchent le venv partagé. Trois fiches de cadrage qui découpent notre agent en trois décisions : l'escalade (règles métier), le classement des incidents (machine learning), la solution tirée de la base de connaissances (RAG réduit à la recherche). La fiche de cadrage du projet est complétée, et le TP1 documenté dans `docs/semaine1.md`. Les 38 tests du TP1 sont repris (environnement, cadrage, historique Git). Commit, étiquette `tp1`, graphe du projet, copie `Agent_support_info_TP1`.

**TP2 : entraîner, évaluer, sauvegarder.** `src/make_demo.py` génère un jeu synthétique anglais avec les 7 catégories IT et une priorité. `src/train.py` découpe à 80/20 avant la vectorisation, entraîne TF-IDF + LinearSVC calibré pour la catégorie et un second modèle pour la priorité, et écrit `models/metrics.json` (versionné). L'option `--reel` entraîne sur Tobi-Bueck, avec les filtres et les règles de tags du notebook. Viennent ensuite `src/evaluate.py` (matrice de confusion), `src/predict.py` (catégorie, confiance, priorité) et `tests/test_model.py`. Le notebook est copié dans `notebooks/`. `docs/semaine2.md` reprend l'analyse du notebook : F1 des 8 queues (0,592), textes courts, catégories tirées des tags, garde-fou de vocabulaire, les 12 incidents.

**TP3 : exposer le modèle par une API.** `api/schemas.py` (contrat Pydantic), `api/model.py` (raccord vers `predict()` et vers la base de connaissances), `api/main.py` (lifespan, `/`, `/health`, `/predict`, `/assist`, `/tickets`, `/tickets/{id}`). La base de connaissances `data/base_connaissances.csv` (au moins 3 articles par catégorie) et sa recherche TF-IDF dans `src/kb.py`. Les tickets sont stockés dans `tickets/tickets.jsonl`, hors Git, chemin configurable. Les groupes d'escalade sont fixés par catégorie. Les tests de l'API sont écrits, la CI entraîne le modèle de démonstration avant les tests, et `docs/semaine3.md` documente le TP.

**TP4 : tests approfondis et qualité.** Le contrat d'entrée est testé aux frontières et avec hypothesis, puis corrigé dans le schéma. L'abstention `INDETERMINE` combine le seuil, mesuré avec `src/courbe_seuil.py`, et le garde-fou de vocabulaire. Le jeu d'or `data/jeu_or.csv` contient 20 incidents, dont au moins 5 difficiles, évalués par `src/bilan_jeu_or.py`. Les tests d'intégration couvrent le démarrage, le modèle absent (503) et les pannes (500), avec une couverture d'au moins 95 %. Le contrat est typé, puis viennent ruff, mypy, pre-commit, la CI étendue et `docs/semaine4.md`.

**TP5 : l'interface Streamlit.** `ui/client.py` traduit chaque réponse de l'API. `ui/app.py` permet de décrire un incident, affiche des étapes cochables et la question « Is it solved? » (oui/non), puis crée le ticket ; un second onglet traite un fichier CSV de tickets. Le TP comprend les tests du client et de la page (AppTest), `data/incidents_exemple.csv` et `docs/semaine5.md`.

**TP6 : packager l'application.** Le paquet `support_it` reçoit `predict.py` par `git mv`, et un fichier de compatibilité reste dans `src/`. L'API importe le paquet sans toucher `sys.path`. La commande `support` (`--version`, `predict`, `assist`, `serve`, `ui`) est ajoutée, ainsi que la variable `SUPPORT_MODELE`. `pyproject.toml` épingle scikit-learn ; la roue est construite puis installée hors du dépôt. Le TP se termine par `tests/test_packaging.py`, `CHANGELOG.md`, les étiquettes `tp6` et `v0.6.0`, et `docs/semaine6.md`.

**À chaque fin de TP** : contrôles du guide avec les chiffres réellement obtenus, documentation, commit, étiquette `tpN`, mise à jour du graphe (`graphify-out/`, hors Git), copie `Agent_support_info_TPn`, comparaison de l'empreinte de `sentiment-app/`.

## Comment ce journal est rempli

Chaque contrôle du guide a son bloc : la commande, l'**attendu** (le chiffre du guide pour `sentiment-app`, ou son équivalent pour notre projet), l'**obtenu** (les lignes utiles de la sortie réelle, jamais recopiées du guide), la case **Conforme**, et un **commentaire** : ce que montre le résultat et, s'il diffère, la cause et la correction. Les captures d'écran ne sont pas produites par Claude Code : la sortie texte les remplace ici, et les captures restent à faire par un humain si l'enseignant les exige (voir « À faire par l'humain »).

## À faire par l'humain

Actions que Claude Code ne fait pas seul (compte, mot de passe, membre B) :

| TP | Action | Qui |
| --- | --- | --- |
| TP1 | Créer le dépôt GitHub **privé** `Agent_support_info` ; inviter le membre B (Write) et l'enseignant `Larhlimiabd-ai` | Membre A |
| TP1 | `git remote add origin https://github.com/<compte-A>/Agent_support_info.git`, `git push -u origin main`, `git push origin --tags` | Membre A |
| TP1 | Cloner, ajouter sa ligne au tableau du binôme dans `README.md`, commiter et pousser (contrôles T4, T5) | Membre B |
| TP1 | Vérifier l'onglet Actions (CI verte) et refaire le clone frais T7 depuis GitHub | Les deux |
| Tous | Captures d'écran dans `docs/captures/` si l'enseignant les exige | Les deux |

## Écarts au guide et à la méthode

| TP | Écart | Raison |
| --- | --- | --- |
| Tous | Aucun kit : chaque fichier est écrit par nous, en s'inspirant de `sentiment-app/` | Consigne du projet |
| Tous | Un seul `.venv` dans le dossier de travail (`..\.venv`), et non dans le dépôt | Consigne du projet : partagé par le dépôt et les copies `Agent_support_info_TPn` |
| TP1 | Le guide du cours est le fichier `guide-rattrapage-tp1-tp6-26-10-2026.pdf`, et non `guide-rattrapage-tp1-tp6-beamer.pdf` | Nom du fichier fourni ; même contenu (125 pages, TP1 à TP6) |
| TP1 | Les énoncés `TPn-ENONCE.md` et les `MARCHE-A-SUIVRE*.md` du cours ne sont pas recopiés dans le dépôt | Ce sont des documents du cours, lus dans `sentiment-app/` ; notre dépôt contient nos propres documents |
| TP1 | Les trois fiches du TP1 portent sur notre sujet (escalade, classement, solutions), pas sur les trois cas du kit (pharmacie, règlement, avis) | Le TP1 demande trois fiches argumentées ; les fiches du kit sont déjà remplies dans `sentiment-app` et ne doivent pas être recopiées |
| TP1 | Le crochet `graphify install --project` demande de lancer `graphify update .` après chaque modification de code : nous ne le faisons pas | Le prompt du projet fixe les mises à jour du graphe à la fin de chaque TP seulement |

---

## 0\. La préparation des postes

### Poste du membre A

```powershell
py -0
py -3.11 --version
git --version
git config --global user.name
```

&nbsp;

**Attendu** : une version 3.11 dans la liste, `Python 3.11.x`, une version de Git, le nom du membre A.

**Obtenu** :

```
 -V:3.14          C:\Users\ANASS\AppData\Local\Programs\Python\Python314\python.exe
 -V:3.11          C:\Users\ANASS\AppData\Local\Programs\Python\Python311\python.exe
Python 3.11.9
git version 2.49.0.windows.1
Aadoud Anass
```

- [x] Conforme

**Commentaire** :

> Python 3.11.9 est installé à côté de 3.14 : le venv est créé explicitement avec `py -3.11`. Au moment du contrôle, le terminal avait le venv de `sentiment-app` actif (marqué `*` par `py -0p`) : nous ne l'utilisons pas, et `DEPANNAGE.md` signale ce cas.

### Poste du membre B

```powershell
py -0
py -3.11 --version
git --version
git config --global user.name
```

&nbsp;

**Attendu** : une version 3.11, `Python 3.11.x`, une version de Git, le nom du membre B, différent de celui du membre A.

**Obtenu** :

```
À compléter par le membre B
```

- [ ] Conforme

**Commentaire** :

> À compléter par le membre B.

---

## TP1 : cadrer l'application et préparer l'environnement

**Date** : 8 novembre 2026 · **Fait par** : membre A (avec Claude Code)

**Ce qui a été fait.** Lecture du guide (125 pages), de la ligne du sujet 9, des sources de méthode de `sentiment-app` (énoncé, marches à suivre, `TESTS.md`, `DEPANNAGE.md`, `AIDE-GIT.md`, cadrage) et du notebook avec ses sorties. Création du `.venv` partagé (Python 3.11.9) dans le dossier de travail et installation de `requirements.txt` (les paquets du semestre, PyTorch compris). Le dépôt `Agent_support_info` a la même structure que `sentiment-app`. Les scripts de mise en place et de diagnostic sont adaptés au venv partagé. Les 38 tests du TP1 sont repris. Trois fiches de cadrage ont été écrites, la fiche du projet complétée, `docs/semaine1.md` rédigé. Quatre commits par étape logique, branche `main`.

**Décisions et raisons.**

- Les trois fiches découpent **notre** agent en trois décisions (escalade : règles métier ; classement : machine learning ; solution : RAG réduit à la recherche) plutôt que de reprendre les cas du kit : elles servent de cahier des charges aux TP suivants, comme la fiche cas3 de `sentiment-app` pour son TP2.
- `check_setup.py` accepte deux venvs : le venv partagé (`..\.venv`) et un venv dans le dépôt, pour que le clone frais (T7) et la CI, qui créent leur propre `.venv`, restent verts. Les tests gardent les mêmes 38 cas que le cours, pour rester comparables au guide ; `tickets/` est vérifié par le diagnostic, pas par un test de plus.
- Le jeu d'exemple `data/exemples_incidents.csv` (28 incidents, 4 par catégorie) remplace `data/sample_reviews.csv` : il est versionné (exception dans `.gitignore`), comme son équivalent.

**Problèmes rencontrés.** Les fiches ont été écrites avant de lancer T1. Pour mesurer quand même l'état de départ du guide, T1 a été rejoué sur une copie temporaire du dépôt dont les trois fiches étaient remises au modèle vide (voir T1). Git signale `LF will be replaced by CRLF` (Windows, `core.autocrlf`) : sans conséquence, comme l'indique le guide.

### T0 · La structure du dépôt (membre A)

```powershell
Get-ChildItem -Force
```

&nbsp;

**Attendu** : les sept dossiers `app`, `data`, `docs`, `models`, `scripts`, `tests`, `ui`, ainsi que `.github` et `.gitignore`.

**Obtenu** :

```
d----- .github   d----- .vscode   d----- app   d----- data   d----- docs   d----- models
d----- scripts   d----- tests     d----- ui
-a---- .editorconfig  .env.example  .gitignore  AIDE-GIT.md  DEPANNAGE.md  Makefile
-a---- pytest.ini  README.md  requirements.txt  TESTS.md
```

- [x] Conforme

**Commentaire** :

> Les sept dossiers, `.github` et `.gitignore` sont là. Pas de kit : la structure a été créée à la main, sur le modèle de l'arborescence de `sentiment-app` (guide, p. 5). Pas de `.venv` dans le dépôt : il est dans le dossier parent.

### T1 · L'environnement et le point de départ (membre A)

```powershell
py -3.11 -m venv ..\.venv                 # depuis le dépôt : le venv partagé
..\.venv\Scripts\Activate.ps1
python --version
pip install -r requirements.txt
python -m pip freeze | Out-File -Encoding utf8 requirements.lock
python scripts/check_setup.py
python -m pytest -q
```

&nbsp;

**Attendu** : `Python 3.11.x` ; une installation sans erreur ; le diagnostic signale encore une erreur ; pytest affiche `3 failed, 31 passed, 4 skipped`.

**Obtenu** :

```
Python 3.11.9
Successfully installed ... scikit-learn-1.5.2 ... streamlit-1.39.1 ... torch-2.15.0 ...   (requirements.lock : 181 lignes)
  OK         environnement virtuel partagé actif (C:\Users\ANASS\OneDrive\Desktop\project\.venv)
  ERREUR     ce dossier n'est pas un dépôt Git : git init ou git clone
Résultat : 1 erreur(s), 0 avertissement(s)

pytest, fiches remises au modèle vide (copie temporaire du dépôt) : 3 failed, 31 passed, 4 skipped in 2.88s
pytest, dépôt réel (fiches déjà remplies)                        : 34 passed, 4 skipped in 3.26s
```

- [x] Conforme

**Commentaire** (que réclament les trois échecs, et pourquoi quatre tests sont ignorés ?) :

> Les trois échecs sont dans `tests/test_cadrage.py` : rubriques vides, aucune case cochée, aucun critère cité. Ils disparaissent une fois les fiches remplies. Les quatre tests ignorés attendent un dépôt Git : trois dans `test_git_history.py`, un dans `test_environment.py` (`.env` non suivi). Le diagnostic n'a qu'une erreur, l'absence de dépôt Git. Le guide en annonce aussi des avertissements (fiches vides), absents ici parce que les fiches étaient déjà remplies.

### T2 · Les fiches de cadrage

```powershell
python -m pytest tests/test_cadrage.py -q
python -m pytest -q
```

&nbsp;

**Attendu** : `12 passed`, puis `34 passed, 4 skipped`.

**Obtenu** :

```
12 passed in 0.04s
34 passed, 4 skipped in 3.26s
```

- [x] Conforme

**Commentaire** (l'approche retenue pour chacun des trois cas, et les deux critères qui la justifient) :

> `cas1-escalade-incidents.md` : règles métier, par (b) la vérifiabilité (une escalade s'explique au technicien) et (d) la conséquence d'une erreur (un incident urgent non escaladé), sans historique étiqueté (a). `cas2-classement-incidents.md` : machine learning, par (a) les 8 266 incidents Tobi-Bueck étiquetés à partir des tags et (c) un coût par requête quasi nul ; (d) est traité par l'abstention. `cas3-solutions-base-connaissances.md` : RAG réduit à la recherche, par (b) la citation de l'article et (d) l'interdiction de toute procédure inventée.

### T3 · Le dépôt et le premier commit (membre A)

```powershell
git init
git add -A
git status
git commit -m "..."          # quatre commits, un par étape logique
git branch -M main
python -m pytest -q
```

&nbsp;

**Attendu** : `git status` ne liste ni `.venv/`, ni `.env`, ni fichier `.joblib` ; pytest affiche `37 passed, 1 failed`.

**Obtenu** :

```
git status --short : 38 fichiers en attente (A), aucune ligne .venv/, .env ou .joblib
a66c1bd TP1 : README, démarche de test, aide Git et dépannage
dda7f6b TP1 : fiche de cadrage du projet complétée et trois fiches cas1 à cas3
26acd90 TP1 : tests d'environnement, de cadrage et d'historique Git (38 tests)
e63c305 TP1 : structure du dépôt, configuration et scripts (venv partagé)
FAILED tests/test_git_history.py::test_each_member_has_committed
1 failed, 37 passed in 3.10s
```

- [x] Conforme (pour la partie locale ; le dépôt GitHub et le `push` sont à faire par un humain)

**Commentaire** (quel test échoue encore, et pourquoi ?) :

> `test_each_member_has_committed` : un seul auteur, `Aadoud Anass`. Le test passera quand le membre B aura commité (T5). Rien de lourd ni de secret n'est suivi. Le `.venv` n'est même pas dans le dossier du dépôt, et `.gitignore` l'exclut quand même. Le dépôt GitHub n'est pas créé : il faut un compte (voir « À faire par l'humain »).

### T4 · Le diagnostic (le membre B le refera sur son poste)

```powershell
python scripts/check_setup.py
```

&nbsp;

**Attendu** : `0 erreur(s)` au diagnostic.

**Obtenu** (poste du membre A, après `git init`) :

```
  OK         dépôt Git détecté
  ATTENTION  1 auteur(s) seulement : les deux membres doivent pousser un commit
  OK         .venv/ n'est pas suivi par Git
Résultat : 0 erreur(s), 1 avertissement(s)
```

- [x] Conforme sur le poste du membre A ; à refaire par le membre B après son clone

**Commentaire** :

> Plus aucune erreur. Le seul avertissement est l'auteur unique, normal à ce stade : il disparaît avec le commit du membre B.

### T5 · Un commit par membre (membres B puis A)

```powershell
git pull
git add README.md
git commit -m "README : ajout de <nom> au tableau du binome"
git push
git shortlog -sn --all
python -m pytest tests/test_git_history.py -q
```

&nbsp;

**Attendu** : deux noms distincts dans `git shortlog`, puis `3 passed`.

**Obtenu** :

```
     4	Aadoud Anass
FAILED tests/test_git_history.py::test_each_member_has_committed - AssertionError
1 failed, 2 passed in 0.35s
```

- [ ] Conforme : **non, en attente du membre B**

**Commentaire** :

> Un seul nom. Le commit du membre B (sa ligne dans le tableau du `README.md`) ne peut pas être fait à sa place : un commit signé de son nom par quelqu'un d'autre fausserait exactement ce que le test vérifie. C'est la première ligne de « À faire par l'humain ».

### T6 · La vérification finale (à deux)

```powershell
git pull
python scripts/check_setup.py
python -m pytest -q
```

&nbsp;

**Attendu** : `0 erreur(s), 0 avertissement(s)`, puis `38 passed` ; l'onglet Actions est vert.

**Obtenu** (avant le commit du membre B) :

```
Résultat : 0 erreur(s), 1 avertissement(s)
1 failed, 37 passed in 3.10s
```

- [ ] Conforme : **non, en attente du membre B et du push**

**Commentaire** :

> L'état obtenu est celui du guide « dépôt initialisé, un seul auteur, fiches remplies » (`TESTS.md`). Il deviendra `38 passed` et `0 avertissement(s)` après le commit du membre B. La CI n'a pas tourné : le dépôt n'est pas encore sur GitHub.

### T7 · Le clone frais

```powershell
cd $env:TEMP
git clone C:\Users\ANASS\OneDrive\Desktop\project\Agent_support_info asi_verif_tp1    # le dépôt local : pas encore de GitHub
cd asi_verif_tp1
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/check_setup.py
python -m pytest -q
```

&nbsp;

**Attendu** : `0 erreur(s)` et `38 passed`, sans aucune intervention.

**Obtenu** :

```
pip install -q -r requirements.txt : aucune erreur
Résultat : 0 erreur(s), 1 avertissement(s)          (l'avertissement : 1 auteur seulement)
FAILED tests/test_git_history.py::test_each_member_has_committed
1 failed, 37 passed in 3.36s
```

- [x] Conforme pour tout ce qui ne dépend pas du membre B ; `38 passed` attend son commit

**Commentaire** (qu'est-ce que ce contrôle prouve que T6 ne prouvait pas ?) :

> Le dépôt tient debout tout seul : un clone neuf, avec son propre `.venv` (accepté par le diagnostic) et une installation depuis `requirements.txt`, donne exactement les mêmes résultats que le poste du membre A. Aucun fichier n'a été oublié dans un commit. Le clone a été fait depuis le dépôt local, et non depuis GitHub, qui n'existe pas encore : le T7 du guide, sur une adresse GitHub, reste à refaire après le push. Le dossier temporaire a été supprimé.

### Résultats du TP1

| Contrôle | Attendu (guide) | Obtenu | Conforme |
| --- | --- | --- | --- |
| T0 | sept dossiers, `.github`, `.gitignore` | idem | oui |
| T1 | 3 failed, 31 passed, 4 skipped | 3 failed, 31 passed, 4 skipped (fiches vides, copie temporaire) | oui |
| T2 | 12 passed, puis 34 passed, 4 skipped | 12 passed, puis 34 passed, 4 skipped | oui |
| T3 | rien d'indésirable ; 37 passed, 1 failed | idem ; push à faire | oui (local) |
| T4 | 0 erreur(s) | 0 erreur(s), 1 avertissement(s) | oui (membre A) |
| T5 | deux noms, 3 passed | un nom, 1 failed, 2 passed | non : membre B |
| T6 | 0 erreur, 0 avertissement, 38 passed, CI verte | 0 erreur, 1 avertissement, 37 passed, 1 failed | non : membre B, push |
| T7 | 0 erreur(s), 38 passed | 0 erreur(s), 37 passed, 1 failed | oui sauf l'auteur unique |

**Ce qui reste à faire par un humain pour finir le TP1** : le dépôt GitHub, le push (avec `--tags`), le commit du membre B, la CI verte, et T7 refait depuis GitHub (tableau « À faire par l'humain »).

### Fin du TP1 : graphe, empreinte, étiquette, copie

**Graphe de notre projet** (`/graphify ./Agent_support_info`, sortie dans `Agent_support_info/graphify-out/`, hors Git) : 155 nœuds, 274 arêtes, 12 groupes (74 nœuds tirés du code, 77 des documents).

**Comparaison avec le graphe de `sentiment-app`** (`graphify-sentiment-app/`, 469 nœuds, 21 groupes) : les groupes du TP1 se retrouvent un pour un. On a des deux côtés « Tests d'environnement », « Tests d'historique Git », « Tests et outils des fiches » (`test_cadrage.py`, `section_body`, `new_cadrage.py`), « Diagnostic check_setup », « Workflow CI » et les scripts `setup.sh` et `verif_clone.sh`. Les fonctions de `check_setup.py` sont les mêmes (`check_python`, `check_packages`, `check_structure`, `check_git`, `check_cadrage`). **Écarts** : les groupes `src/`, `api/`, `ui/` et `sentiment_app/` de la référence n'ont pas encore d'équivalent. C'est normal au TP1, ils arrivent aux TP2 à TP6. Notre graphe a en plus un groupe « Cadrage et décisions de l'agent » qui relie les trois fiches à la fiche du projet, parce que nos fiches portent sur un seul projet, alors que celles du kit portaient sur trois cas sans lien.

**Empreinte de `sentiment-app/`** : `Compare-Object` entre `empreinte_sentiment_app.csv` (prise avant tout travail) et l'état de fin de TP1 : 58 813 fichiers avant, 58 813 après, **aucune différence**.

**Étiquette** `tp1` sur le dernier commit du TP1, puis copie `Agent_support_info_TP1` (robocopy, sans caches ni `graphify-out/`).
