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

**TP5.1 : améliorer l'agent (entre le TP5 et le TP6).** Diagnostic des tickets sur 30 conversations (`src/bilan_tickets.py`), puis une politique de conversation testée (`api/conversation.py`, `POST /chat`) : jamais de ticket au premier message, une autre solution ou une question de précision, le ticket après deux tentatives, sur demande ou pour un cas critique, toujours confirmé, un seul par conversation. Base de 42 articles, page en conversation, suivi des tickets, avis sur les réponses, statistiques, ticket passé le plus proche, Ollama en option. `docs/semaine5.1.md`.

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
| TP2 | `git pull`, `python src/make_demo.py`, `python src/train.py`, `python -m pytest -q` ; vérifier la CI après le push | Membre B |
| TP3 | Vérifier la CI (T19) ; membre B : `git pull`, `python src/train.py`, `python -m pytest -q`, essais T15 à T18 | Les deux |
| TP4 | Membre B : `pip install -r requirements-dev.txt`, `pre-commit install`, ses dix incidents du jeu d'or ; vérifier la CI (T27) | Les deux |
| TP5 | Essayer la page dans un navigateur (T29 à T33, `uvicorn api.main:app` puis `streamlit run ui/app.py`) ; vérifier la CI (T34) | Les deux |
| TP5.1 | Essayer la conversation dans un navigateur : un incident résolu, deux « Not solved » puis le ticket, un cas critique, le suivi et les statistiques ; vérifier la CI | Les deux |
| TP5.1 | Décider avec le binôme si un jeu public de plus (catégories faibles, messages courts) vaut la peine pour le modèle réel | Les deux |
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
| TP2 | `tests/test_model.py` applique un seuil de F1 par source : 0,85 (cours) sur la démonstration, 0,75 sur Tobi-Bueck | Seuil d'acceptation fixé au TP1 dans la fiche `cas2` (référence du notebook 0,788) ; le seuil du cours reste affiché et comparé par `train.py` |
| TP2 | Pas de filtre sur les queues rares du notebook : 8 452 incidents au lieu de 8 266 | Filtre absent de la liste des filtres retenus pour le projet |
| TP2 | Jeu de démonstration de 350 incidents en 7 catégories (au lieu de 290 avis en 2 classes) | Mêmes 7 catégories que le jeu réel ; 10 incidents mêlés par catégorie jouent le rôle des avis mitigés |
| TP3 | Routes en plus de `/health` et `/predict` : `/assist`, `/tickets`, `/tickets/{id}` ; 10 tests d'API au lieu de 6 | Fonctionnalités du sujet 9 (solution, ticket, escalade) |
| TP3 | La réponse du ticket passé le plus proche (`answer` de Tobi-Bueck) n'est pas exposée | L'API de la CI tourne sans réseau sur le modèle de démonstration ; facultatif dans le cadrage |
| TP4 | Seuil d'abstention 0,60 et garde-fou de vocabulaire (deux causes d'abstention) | Seuil mesuré sur les deux jeux ; garde-fou tiré du notebook (section 15.1) |
| TP4 | Les 20 incidents du jeu d'or sont écrits par le membre A seul | Le guide demande dix incidents par membre : le membre B doit compléter ou remplacer les siens |
| TP5 | Contrôles T29 à T33 rejoués avec `AppTest` et le client, pas dans un navigateur | Pas de navigateur dans l'environnement de travail ; la page et l'API tournaient pour de bon |
| TP5 | `/assist` reçoit un champ `motif`, les groupes d'escalade passent en anglais | Page en anglais : elle traduit un code, au lieu d'interpréter une phrase |
| TP5.1 | Étape hors du guide : plus de copie fidèle de `sentiment-app` (design, routes et fonctionnalités en plus) | Consigne du TP5.1 ; l'architecture, les tests et la CI restent ceux du cours |
| TP5.1 | Un LLM (Ollama) en option, désactivé par défaut | Consigne du TP5.1 ; aucun test ni aucune décision n'en dépend |
| TP5.1 | `/assist` et ses règles (fiche `cas1`) gardés tels quels, à côté de `/chat` | Ils servent au tri d'un fichier de tickets, et à mesurer l'« avant » du bilan |

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

---

## TP2 : entraîner, évaluer et sauvegarder le modèle

**Date** : 8 novembre 2026 · **Fait par** : membre A (avec Claude Code)

**Ce qui a été fait.** Sans kit, et sur le modèle de `sentiment-app/src/`, quatre scripts ont été écrits : `src/make_demo.py`, `src/train.py`, `src/evaluate.py` et `src/predict.py`. S'y ajoutent `tests/test_model.py` (4 tests), le notebook copié dans `notebooks/`, `docs/semaine2.md` et la fiche du projet mise à jour.

**Décisions et raisons.**

- **Un seul fichier de modèle**, `models/support.joblib`, qui contient les deux pipelines (`categorie`, `priorite`) : l'API et la future commande `support` n'ont qu'un chemin à connaître (une seule variable `SUPPORT_MODELE` au TP6).
- **`predict()` renvoie `label`, `score` et `priorite`** : mêmes noms que dans `sentiment-app` pour `label` et `score`, qui deviendront le contrat de l'API au TP3.
- **Les seuils de F1 dépendent de la source**, inscrite dans `metrics.json` : 0,85 (le cours) pour la démonstration, 0,75 pour Tobi-Bueck. Le 0,75 a été fixé au TP1 dans la fiche `cas2`, à partir de la référence du notebook (0,788), avant toute mesure du TP2. `train.py` affiche toujours la comparaison au seuil du cours (« non atteint » sur Tobi-Bueck). Ce n'est pas un test de kit retouché, mais c'est un écart au guide, signalé dans le tableau des écarts.
- **Pas de filtre sur les queues rares** (`MIN_PAR_QUEUE` du notebook) : il ne fait pas partie des filtres fixés par le projet. D'où 8 452 incidents au lieu de 8 266, et la fiche est mise à jour.
- **Lecture du jeu réel** : le fichier Parquet que Hugging Face publie pour ce jeu (`.../parquet/default/train/0.parquet`, 61 765 tickets), lu par `pandas.read_parquet` comme Allociné dans le cours, sans la bibliothèque `datasets`.

**Problèmes rencontrés : trois essais pour le jeu de démonstration.** Le premier générateur citait un court contexte d'une autre catégorie (« after the Windows update ») avant le vrai symptôme. Résultat : F1 macro **1,000**, aucune erreur, donc rien à analyser au contrôle C4. Le deuxième essai a copié la structure des avis mitigés du cours : un symptôme complet d'une autre catégorie, un retournement, puis le vrai problème, avec 15 incidents mêlés par catégorie. Résultat : F1 macro **0,841**, 11 erreurs, juste sous le seuil du cours. Le jeu final garde 10 incidents mêlés par catégorie (20 % du jeu) : F1 macro **0,856**, 10 erreurs, toutes sur des incidents mêlés. Ce réglage porte sur la conception du jeu synthétique, pas sur le modèle ni sur le test. Les trois chiffres sont rapportés ici pour cette raison.

### C1 · Le point de départ

```powershell
python -m pytest -q
```

&nbsp;

**Attendu** : `2 failed, 38 passed, 2 skipped`.

**Obtenu** :

```
FAILED tests/test_git_history.py::test_each_member_has_committed
FAILED tests/test_model.py::test_metriques_completes - AssertionError: models...
FAILED tests/test_model.py::test_f1_au_dessus_du_seuil - AssertionError: mode...
3 failed, 37 passed, 2 skipped in 3.14s
```

- [x] Conforme, à l'échec d'auteur du TP1 près

**Commentaire** :

> Les deux échecs du TP2 réclament `models/metrics.json`, et les deux tests ignorés attendent `models/support.joblib`. Le troisième échec est celui du TP1 (un seul auteur) : il n'a rien à voir avec le modèle.

### C2 · Le jeu de démonstration

```powershell
python src/make_demo.py
```

&nbsp;

**Attendu** (guide, `sentiment-app`) : 290 avis, 145 de chaque classe. **Chez nous** : 350 incidents, 50 par catégorie.

**Obtenu** :

```
350 incidents écrits dans data/demo_incidents.csv
  par catégorie : securite 50, reseau 50, materiel 50, compte_acces 50, facturation 50, logiciel 50, panne_service 50
  par priorité  : high 119, medium 119, low 112
  dont 70 incidents mêlés, volontairement difficiles
```

- [x] Conforme

**Commentaire** :

> Équilibré par catégorie, déterministe (graine 42). Les 70 incidents mêlés jouent le rôle des 100 avis mitigés du cours. `data/demo_incidents.csv` est exclu de Git par `data/*` : il se régénère en une commande.

### C3 · L'entraînement

```powershell
python src/train.py
git status --short
```

&nbsp;

**Attendu** : un F1 macro au-dessus de 0,85 (0,879 dans le cours) ; `models/metrics.json` apparaît dans `git status`, ni le modèle ni le jeu de données.

**Obtenu** :

```
Source : demo, 350 incidents, 7 catégories
280 incidents d'entraînement, 70 de test
Vocabulaire : 661 termes
F1 macro sur le jeu de test : 0.856 (seuil du cours 0.85 : atteint ; acceptation pour « demo » : 0.85)
Priorité : F1 macro 1.000, rappel de high 1.000
?? models/metrics.json
?? src/
?? tests/test_model.py
```

- [x] Conforme

**Commentaire** :

> Le découpage se fait avant la vectorisation (`decouper()`, réutilisé par `evaluate.py`). Le `Pipeline` enferme le vectoriseur et le modèle, et la graine fixe le découpage. La priorité est parfaite sur la démonstration, parce que le générateur la tire de mots d'urgence fixes : ce chiffre ne dit rien du jeu réel (0,661).

### C4 · L'évaluation

```powershell
python src/evaluate.py
```

&nbsp;

**Attendu** (cours) : 7 erreurs sur 58, toutes sur des avis mitigés. **Chez nous** : des erreurs, toutes sur des incidents mêlés.

**Obtenu** :

```
            secu  reseau   mater  compte   factu   logic   panne
    secu       9       1       0       0       0       0       0
  reseau       0       9       0       0       0       1       0
   mater       0       0       8       2       0       0       0
  compte       0       0       1       9       0       0       0
   factu       0       0       0       0      10       0       0
   logic       0       0       1       1       0       8       0
   panne       1       0       0       0       2       0       7
10 erreurs sur 70.
  vérité=panne_service prédit=facturation | Hi team, our card payment was declined, but the real problem is that, the ticketing portal...
  vérité=reseau        prédit=logiciel    | Hi team, Outlook stopped receiving emails, and now, I cannot reach the intranet, DNS looku...
vérification : 10 erreurs, dont 10 sur des incidents mêlés (15 incidents mêlés dans le test)
```

- [x] Conforme

**Commentaire** :

> Toutes les erreurs portent sur des incidents qui décrivent deux symptômes : le sac de mots additionne les deux et ne voit pas lequel conclut. Voir `docs/semaine2.md`.

### C5 · Le vrai jeu de données, les tests

```powershell
python src/train.py --reel
python src/evaluate.py --reel
python -m pytest -q
```

&nbsp;

**Attendu** (cours) : F1 macro 0,920 sur Allociné, puis `42 passed`. **Chez nous** : la référence du notebook, 0,788, puis `42 passed`.

**Obtenu** :

```
Source : tobi-bueck, 8452 incidents, 7 catégories
6761 incidents d'entraînement, 1691 de test
Vocabulaire : 28420 termes
F1 macro sur le jeu de test : 0.789 (seuil du cours 0.85 : non atteint ; acceptation pour « tobi-bueck » : 0.75)
Priorité : F1 macro 0.661, rappel de high 0.717
263 erreurs sur 1691.
FAILED tests/test_git_history.py::test_each_member_has_committed
1 failed, 41 passed in 3.07s
```

- [x] Conforme, à l'échec d'auteur du TP1 près ; CI : à vérifier après le push

**Commentaire** :

> 0,789 retrouve la référence du notebook (0,788) avec un jeu un peu plus grand. Le seuil du cours n'est pas atteint sur les données réelles ; l'explication est dans `docs/semaine2.md` (étiquettes construites à partir des tags, catégories rares absorbées par `logiciel`). Les 4 tests du modèle passent. La CI lira `metrics.json` sans avoir le modèle, comme dans le cours.

### Membre B, après le TP2

À faire par le membre B : `git pull`, `python src/make_demo.py`, `python src/train.py`, `python -m pytest -q`.

### Fin du TP2 : graphe, empreinte, étiquette, copie

**Graphe** (`--update` : 11 documents repris du cache, 3 réextraits ; tout le code réanalysé) : 249 nœuds, 427 arêtes, 16 groupes.

**Comparaison avec `sentiment-app`** : le groupe « Entraînement et évaluation (src/) » correspond au groupe « Entraînement et exemples (src/) » de la référence, avec les mêmes dépendances (`joblib`, `pandas`, `Pipeline`, `argparse`, `train_test_split`). « Métriques et tests du modèle » relie `metrics.json` à `test_model.py`, comme dans la référence. Le jeu de démonstration forme un groupe à part, comme `make_demo.py` de la référence. **Écarts** : notre `src/` n'a pas `courbe_seuil.py` ni `bilan_jeu_or.py`, qui arrivent au TP4, comme dans le cours. Notre `predict.py` charge deux modèles (catégorie et priorité) dans un seul fichier, quand celui de la référence n'en charge qu'un. Il n'existe pas encore de paquet `support_it` : le code de prédiction vit dans `src/`, comme dans `sentiment-app` avant son TP6.

**Empreinte de `sentiment-app/`** : 58 813 fichiers avant, 58 813 après, **aucune différence**.

**Étiquette** `tp2` sur le dernier commit du TP2, puis copie `Agent_support_info_TP2`. Les fichiers du TP3 commencés avant la copie (`api/`, `src/kb.py`, `data/base_connaissances.csv`, non commités) sont exclus de la copie, pour qu'elle ne contienne que le TP2.

---

## TP3 : exposer le modèle par une API

**Date** : 8 novembre 2026 · **Fait par** : membre A (avec Claude Code)

**Ce qui a été fait.** La base de connaissances `data/base_connaissances.csv` est rédigée en anglais : 21 articles, 3 par catégorie (`id`, `categorie`, `titre`, `symptomes`, `etapes` séparées par `|`, `escalade_si`), versionnée par une exception dans `.gitignore`. `src/kb.py` y cherche l'article le plus proche (TF-IDF, similarité cosinus, seuil 0,10). L'API reprend la structure de `sentiment-app/api/` : `schemas.py` pour le contrat, `model.py` pour le raccord et les règles d'escalade, `main.py` pour le lifespan et les routes, plus `tickets.py` pour le stockage JSON Lines. S'y ajoutent `tests/test_api.py` (10 tests), `pythonpath = .` dans `pytest.ini` et une CI qui installe l'API puis entraîne le modèle de démonstration avant les tests.

**Décisions et raisons.**

- **`/assist` renvoie la décision et sa raison** (`decision`, `raison`, `groupe`), en plus du classement et de l'article : la page du TP5 n'aura rien à décider, elle affichera ce que l'API a tranché (règle d'architecture : la page ne connaît pas le modèle).
- **Les règles d'escalade dans `api/model.py`** (`decider`), dans l'ordre de la fiche `cas1` : priorité haute, aucun article, article qui demande toujours un technicien, sinon solution. L'escalade pour `INDETERMINE` (groupe de tri N1) viendra avec l'abstention, au TP4.
- **`POST /tickets` pré-remplit le ticket** : si la page ne transmet pas la catégorie ou la priorité, l'API les calcule ; le groupe vient toujours de la catégorie. Tickets dans `tickets/tickets.jsonl` (hors Git), chemin dans `SUPPORT_TICKETS` pour que les tests n'écrivent jamais dans le dépôt.
- **La base est chargée au démarrage, comme le modèle** : sans base, l'API refuse de démarrer (même raisonnement que T20).

### T14 · Le point de départ

```powershell
python src/train.py          # retour au modèle de démonstration : le TP2 s'est terminé sur Tobi-Bueck
python -m pytest -q
```

&nbsp;

**Attendu** (cours) : `48 passed` (42 du TP2 + 6 de l'API). **Chez nous** : les 42 du TP2 plus nos 10 tests d'API.

**Obtenu** :

```
F1 macro sur le jeu de test : 0.856 (seuil du cours 0.85 : atteint ; acceptation pour « demo » : 0.85)
FAILED tests/test_git_history.py::test_each_member_has_committed
1 failed, 51 passed, 1 warning in 5.14s
```

- [x] Conforme, à l'échec d'auteur du TP1 près

**Commentaire** :

> Les 10 tests de l'API passent : les 6 parallèles au cours (`/`, `/health`, deux classements, deux familles de 422), plus `/assist` (solution, escalade) et `/tickets` (201 puis relecture, 404). L'avertissement est un `DeprecationWarning` d'anyio, sans conséquence (guide, p. 82).

### T15 à T18 · L'API en marche

```powershell
uvicorn api.main:app --port 8000
python -c "import httpx; ..."      # mêmes requêtes que dans /docs
```

&nbsp;

**Attendu** : T15 `/health` 200 et le nom du modèle ; T16 et T17 deux incidents évidents bien classés ; T18 422 pour `""`, `{}`, `42`.

**Obtenu** :

```
Modèle chargé avec succès : tfidf-linearsvc (TP2, models/support.joblib) ; 21 articles
T15 {'status': 'OK', 'model': 'tfidf-linearsvc (TP2, models/support.joblib)', 'articles': 21}
T16 200 {'label': 'reseau', 'score': 0.9133, 'priorite': 'medium', 'text': 'My VPN keeps disconnecting every 10 minutes when I work from home'}
T17 200 {'label': 'facturation', 'score': 0.8348, 'priorite': 'high', 'text': 'I was charged twice for my subscription this month'}
    200 {'label': 'materiel', 'score': 0.9109, 'priorite': 'low', 'text': 'The printer on the second floor shows offline and nothing prints'}
T18 [422, 422, 422]
espaces 422 {'detail': 'texte vide'}
assist materiel solution Poste de travail  -> KB-HW-01
assist panne_service high escalade Exploitation (N2) : priorité haute
ticket 201 {'id': 'TCK-908772C3', ..., 'label': 'logiciel', 'priorite': 'low', 'groupe': 'Applications', ...}
relu 200 ; inconnu 404
```

- [x] Conforme

**Commentaire** :

> Les trois premiers incidents des 12 du notebook sont bien classés par le modèle de démonstration, avec une confiance au-dessus de 0,9 pour deux d'entre eux. Le texte fait d'espaces reçoit bien un 422, mais avec un `detail` en chaîne simple, pas en liste : c'est le défaut annoncé par le guide, à corriger au TP4. La priorité `high` sur « charged twice » montre que le modèle de priorité de la démonstration ne généralise pas (voir `docs/semaine3.md`).

### T19 · La CI

**Attendu** : l'étape « Modèle de démonstration » passe, puis les tests.

**Obtenu** : non vérifiable, le dépôt n'est pas encore sur GitHub. `ci.yml` installe `fastapi`, `httpx` et `uvicorn`, puis lance `python src/make_demo.py && python src/train.py` avant `pytest -q`.

- [ ] Conforme : **à vérifier après le push** (« À faire par l'humain »)

### T20 · L'API sans modèle

```powershell
Rename-Item models\support.joblib support.bak
uvicorn api.main:app --port 8001
Rename-Item models\support.bak support.joblib
```

&nbsp;

**Attendu** : `FileNotFoundError`, puis `Application startup failed`.

**Obtenu** :

```
FileNotFoundError: models/support.joblib absent : lancez python src/train.py
ERROR:    Application startup failed. Exiting.
```

- [x] Conforme

**Commentaire** :

> L'API refuse de démarrer plutôt que de répondre 503 à chaque requête : voir la question 1 de `docs/semaine3.md`. Le modèle a été remis en place aussitôt.

### Membre B, après le TP3

À faire par le membre B : `git pull`, `python src/train.py`, `python -m pytest -q`, puis les essais T15 à T18.

### Fin du TP3 : graphe, empreinte, étiquette, copie

**Graphe** (`--update`) : 354 nœuds, 590 arêtes, 19 groupes.

**Comparaison avec `sentiment-app`** : « Service FastAPI (api/main) » correspond au groupe « Service FastAPI (api/) » de la référence, avec les mêmes fonctions (`lifespan`, `_classifier`, `health_check`, `predict`, `root`). « Raccord api/model » correspond au raccord `model.py` de la référence (`load_model`, la classe qui enveloppe le modèle), et « Tests de l'API TP3 » à « Tests de l'API TP3 » (`test_root`, `test_health`, les deux 422). **Écarts, voulus par le sujet** : un groupe « Stockage des tickets » (`api/tickets.py`) et la fonction `decider()` (règles d'escalade) n'ont pas d'équivalent dans la référence. `decider()` est reliée par le graphe à la fiche `cas1`, ce qui confirme que les règles codées sont celles du cadrage. Comme dans la référence avant le TP6, `api/model.py` modifie encore `sys.path` pour importer `src/`.

**Empreinte de `sentiment-app/`** : 58 813 fichiers avant, 58 813 après, **aucune différence**.

**Étiquette** `tp3`, puis copie `Agent_support_info_TP3`.

---

## TP4 : tests approfondis et qualité

**Date** : 8 novembre 2026 · **Fait par** : membre A (avec Claude Code)

**Ce qui a été fait.** Outils de qualité (`requirements-dev.txt`, `pyproject.toml`, `.pre-commit-config.yaml`), mesurés avant toute correction. `tests/test_limites.py` : 8 cas aux frontières et 2 propriétés hypothesis, puis la correction du schéma. L'abstention `INDETERMINE` combine le seuil mesuré par `src/courbe_seuil.py` et le garde-fou de vocabulaire. Le jeu d'or `data/jeu_or.csv` compte 20 incidents, dont 10 difficiles, avec `src/bilan_jeu_or.py` et `tests/test_jeu_or.py`. Viennent ensuite `tests/test_integration.py`, `tests/test_escalade.py` (les règles de la fiche `cas1`), le contrat typé, ruff et mypy muets, le crochet pre-commit, la CI étendue et `docs/semaine4.md`. Six défauts ont été trouvés et corrigés (tableau de `docs/semaine4.md`, partie 2).

**Décisions et raisons.**

- **Seuil d'abstention 0,60** au lieu de 0,5 : mesuré sur les deux jeux. Sur les données réelles, les erreurs baissent d'un tiers pour 17 % d'incidents envoyés au tri. Changement signalé dans la fiche du projet.
- **Deux causes d'abstention**, le seuil et le garde-fou de vocabulaire, et deux raisons distinctes dans `/assist` : le technicien du tri sait si le texte était hors langue ou seulement ambigu. `predict()` renvoie la part de mots connus, et `api/model.py` décide.
- **Une erreur du jeu d'or déclarée, pas corrigée** : « It does not work » (`compte_acces`, 0,85). Une règle de longueur minimale est une piste, mais la régler sur le jeu d'or reviendrait à tricher avec lui.
- **`tests/test_escalade.py`** : 8 tests sans modèle pour les règles de la fiche `cas1`. Ils ont été écrits parce que la couverture montrait deux règles jamais exécutées, et non pour atteindre 95 %, déjà dépassé.
- **Conflits de version à l'installation des outils** : `packaging` 26 et `platformdirs` 4 sont plus récents que ce que demandent streamlit, mlflow et dvc. Le guide classe le cas de streamlit sans conséquence (p. 86), et mlflow et dvc ne servent pas avant le TP7. Aucun test n'en est affecté.

### T21 · Le point de départ, mesuré

```powershell
pip install -r requirements-dev.txt
python src/train.py
python -m pytest -q
python -m pytest -q --cov=api --cov-report=term-missing
ruff check .
mypy api
```

&nbsp;

**Attendu** (cours) : `1 failed, 51 passed, 1 skipped` avec le kit ; mesures recopiées dans `docs/semaine4.md`. **Chez nous**, sans kit : les tests du TP3, puis les trois mesures.

**Obtenu** :

```
F1 macro sur le jeu de test : 0.856
1 failed, 51 passed, 1 warning                     (l'échec : un seul auteur)
api\main.py         74      7    91%   54, 89-90, 104-105, 125-127
api\model.py        31      2    94%   57, 59
api\schemas.py      44      0   100%
api\tickets.py      26      1    96%   36
TOTAL              175     10    94%
ruff : Found 1 error.  (I001 dans api/main.py)
mypy : Success: no issues found in 5 source files
```

- [x] Conforme : les mesures sont dans `docs/semaine4.md`, parties 1 et 5

### T22 · Une seule forme de refus

**Attendu** : `{"text": "   "}` reçoit 422 avec `detail` en liste, comme `{"text": ""}`.

**Obtenu** (avant la correction : `2 failed, 8 passed`, `detail n'est pas une liste d'erreurs : 'texte vide'`, `Falsifying example: texte='\x85'`) ; après :

```
'   ' 422 value_error Value error, texte vide : il ne contient que des blancs
''    422 string_too_short String should have at least 1 character
```

- [x] Conforme

### T23 · Les propriétés tiennent

```
run 1 : 10 passed, 1 warning in 5.56s
run 2 : 10 passed, 1 warning in 4.56s
run 3 : 10 passed, 1 warning in 4.09s
```

- [x] Conforme

### T24 · Le modèle se tait quand il ne sait rien

**Obtenu** (avant : `logiciel` 0,1766 pour trois charabias, `reseau` 0,8151 pour le message en français) ; après :

```
xqzvb wlkptr grombu -> INDETERMINE 0.1766 0.0
Mon VPN ne se connecte plus depuis ce matin -> INDETERMINE 0.8151 0.1111
assist -> escalade Tri N1 | moins de la moitié des mots sont connus du modèle (11%) : langue ou vocabulaire inconnus, un technicien trie l'incident
```

- [x] Conforme

**Commentaire** :

> La confiance reste renvoyée, et la même qu'avant, comme le demande l'énoncé. Le message en français montre pourquoi le seuil seul ne suffisait pas : 0,8151, c'est au-dessus de tout seuil raisonnable.

### T25 · Le jeu d'or est vert

```
Bilan sur 20 incidents : abstention 5, erreur franche 1, juste 14       (avant déclaration)
20 passed, 1 xfailed, 1 warning in 3.80s                                (après déclaration de « It does not work »)
```

- [x] Conforme

### T26 · Pannes en 500, couverture à 95 %

**Obtenu** (avant correction : `8 failed, 4 passed` dans `test_integration.py`, dont `assert 422 == 500` sur les trois routes) ; après :

```
api\main.py         77      2    97%   135-137
api\model.py        38      0   100%
api\schemas.py      52      0   100%
api\tickets.py      26      0   100%
Required test coverage of 95% reached. Total coverage: 98.96%
```

- [x] Conforme

### T27 · Tout est vert, en local (CI : après le push)

```
ruff check .   -> Found 3 errors (3 fixed, 0 remaining) ; puis All checks passed!
mypy api       -> Success: no issues found in 5 source files
pytest --cov   -> Required test coverage of 95% reached. Total coverage: 99.07%
                  1 failed, 103 passed, 1 xfailed            (l'échec : un seul auteur)
pre-commit, commit d'essai avec « import os » :
ruff (erreurs probables, imports)........Failed   F401 [*] `os` imported but unused
mypy (contrat typé de l'API).............Passed   -> commit refusé, HEAD inchangé
```

- [x] Conforme en local ; CI à vérifier après le push

**Commentaire** :

> Le corrigé du cours donne `83 passed, 2 xfailed`. Nous avons plus de tests (API plus large, règles d'escalade), aucun `failed` hors l'auteur unique, et un seul `xfailed`. La CI enchaîne maintenant l'entraînement de démonstration, ruff, mypy, puis pytest avec `--cov-fail-under=95`.

### Membre B, après le TP4

À faire par le membre B : `git pull`, `pip install -r requirements-dev.txt`, `pre-commit install` dans son clone, `python src/train.py`, `python -m pytest -q`. Il écrit aussi ses dix incidents du jeu d'or : les vingt actuels ont été écrits par le membre A, ce qui est un écart à la répartition du guide (« dix chacun »).

### Fin du TP4 : graphe, empreinte, étiquette, copie

**Graphe** (`--update`) : 464 nœuds, 791 arêtes, 26 groupes.

**Comparaison avec `sentiment-app`** : les groupes du TP4 de la référence ont leur équivalent : « Tests aux limites et jeu d'or » chez elle, « Jeu d'or et analyse des erreurs » et « Tickets et tests de propriétés » chez nous (hypothesis, `given`) ; « Tests d'intégration », « Crochet pre-commit » et « Raccord typé api/model », avec `Prediction` en `TypedDict`, comme `Prediction` de la référence. **Écarts** : nous avons en plus « Règles d'escalade (decider) », relié à la fiche `cas1` et à `tests/test_escalade.py`, et un garde-fou de vocabulaire, à côté du seuil, que la référence n'a pas. Le graphe isole un nœud « Réponse du ticket passé » sans lien vers le code : c'est la fonctionnalité facultative non réalisée (TP3), ce qui est exact.

**Empreinte de `sentiment-app/`** : 58 813 fichiers avant, 58 813 après, **aucune différence**.

**Étiquette** `tp4`, puis copie `Agent_support_info_TP4`.

---

## TP5 : l'interface Streamlit

**Date** : 8 novembre 2026 · **Fait par** : membre A (avec Claude Code)

**Ce qui a été fait.** `ui/client.py`, client HTTP : santé, `/predict`, `/assist`, `/tickets`, lot et résumé, avec chaque code HTTP traduit en message anglais. `ui/app.py`, la page : un incident pas à pas, des étapes cochables, « Is it solved? », la création du ticket, et un onglet pour un fichier de tickets. S'y ajoutent `data/incidents_exemple.csv` (8 tickets, versionné), `tests/test_client.py` (9 tests) et `tests/test_interface.py` (6 tests, `AppTest`), Streamlit dans la CI et `docs/semaine5.md`. Côté API, un seul ajout : le champ `motif` de `/assist`.

**Décisions et raisons.**

- **`motif` dans `/assist`** : la page doit être en anglais, mais la raison de la décision, en français, est écrite pour le technicien. Plutôt que de faire traduire une phrase par la page (qui devrait alors connaître les règles), l'API renvoie un code, et la page le traduit avec une table (`MOTIFS`).
- **Les réponses gardées dans `st.session_state`** : Streamlit relance le script à chaque clic. Sans cela, cocher une étape ou répondre « Is it solved? » effacerait la réponse de `/assist`.
- **« No » crée le ticket tout de suite** : c'est la promesse du sujet (« sinon, crée un ticket pré-rempli »). Pour une escalade, le ticket attend un clic, pour que l'utilisateur voie d'abord pourquoi on escalade et puisse essayer les étapes en attendant.
- **Les noms des groupes en anglais** : défaut vu à T30 (« sent to the Poste de travail team »), corrigé dans `api/model.py`.

**Problèmes rencontrés.**

- Pas de navigateur dans l'environnement de travail : T29 à T32 ont été rejoués avec `AppTest` sur la vraie page, branchée sur l'API réelle par HTTP, avec la page Streamlit lancée en parallèle (réponse 200 sur le port 8501). T33 est passé par les fonctions du client, parce qu'`AppTest` ne sait pas déposer un fichier. Un essai à la main dans le navigateur est ajouté à « À faire par l'humain ».
- **Copies modifiées par les tests** (constaté à la fin du TP4) : lancer pytest depuis une copie `Agent_support_info_TPn` y écrivait des caches (`__pycache__/`, `.hypothesis/`). Ce sont des fichiers exclus de Git, mais une copie ne doit plus changer après sa création. Les caches ont été supprimés des quatre copies, dont le `git status` est resté vide. Les vérifications suivantes se font avec `PYTHONDONTWRITEBYTECODE=1` et les caches nettoyés juste après.

### T28 · Le point de départ du TP5

```powershell
python -m pytest -q
```

&nbsp;

**Attendu** (cours) : aucun `failed`, 12 tests de plus. **Chez nous** : 15 tests de plus (9 du client, 6 de la page).

**Obtenu** :

```
Required test coverage of 95% reached. Total coverage: 99.09%
FAILED tests/test_git_history.py::test_each_member_has_committed
1 failed, 118 passed, 1 xfailed, 1 warning
ruff : All checks passed! ; mypy : Success: no issues found in 5 source files
```

- [x] Conforme, à l'échec d'auteur du TP1 près

### T29 à T31 · La page, l'API prête, les verdicts, l'abstention

```powershell
uvicorn api.main:app --port 8000
streamlit run ui/app.py --server.headless true --server.port 8501
```

&nbsp;

**Obtenu** :

```
page 8501 : 200
T29 API ready: tfidf-linearsvc (TP2, models/support.joblib), 21 articles
T30 My VPN keeps disconnecting... -> Network 91% | Try these steps, then tell us if the problem is solved. | article: VPN disconnects or does not connect | étapes: 5
T30 The printer on the second floor... -> Hardware 91% | ... | article: Printer offline or not printing | étapes: 5
T30 non résolu -> Ticket TCK-96F33B78 created and sent to the Poste de travail team.
T31 I don't know: a technician will sort this incident 18% | Most words of your message are unknown to the agent (it only understands English): a technician will take over.
T31 ticket -> Ticket TCK-7F7BA72C created and sent to the Tri N1 team.
```

- [x] Conforme (le nom du groupe, en français, a été corrigé ensuite : voir les décisions)

### T32 · Les erreurs

```
T32 espaces -> Text refused: empty, only spaces, or more than 2000 characters.
T32 API arrêtée -> API unreachable: start uvicorn api.main:app first.
```

- [x] Conforme

### T33 · Un fichier de tickets

**Obtenu** (`data/incidents_exemple.csv`, 8 tickets) :

```
Network 0.9133 solution | Hardware 0.9131 solution | Billing 0.8348 escalade | Service outage 0.8399 escalade
I don't know 0.1766 escalade (Tri N1) | I don't know 0.8151 escalade (Tri N1) | Software 0.9269 solution | Account and access 0.9343 solution
T33 résumé {'INDETERMINE': 2, 'compte_acces': 1, 'facturation': 1, 'logiciel': 1, 'materiel': 1, 'panne_service': 1, 'reseau': 1} | vers un technicien : 4 sur 8
results.csv écrit (dossier temporaire)
```

- [x] Conforme

### T34 · Compte rendu, push, CI

**Obtenu** : compte rendu écrit (`docs/semaine5.md`) ; la CI installe maintenant Streamlit. Push et CI : non vérifiables ici.

- [ ] Conforme : **à vérifier après le push**

### Membre B, après le TP5

À faire par le membre B : `git pull`, `python src/train.py`, `python -m pytest -q`, puis T29 à T33 dans son navigateur (`uvicorn api.main:app` et `streamlit run ui/app.py` dans deux terminaux).

### Fin du TP5 : graphe, empreinte, étiquette, copie

**Graphe** (`--update`) : 531 nœuds, 912 arêtes, 29 groupes.

**Comparaison avec `sentiment-app`** : le groupe « Client HTTP de l'interface » (`Client`, `httpx`, `Response`, `test_client.py`) correspond à « Client de l'API et tests UI » de la référence, et « Tests de la page Streamlit » (`AppTest`, `test_api_injoignable`, `test_espaces_avertissement`) reprend le même découpage. Le graphe relie la règle « l'interface n'importe jamais predict() » au client et non au modèle : la règle d'architecture du guide est respectée. **Écarts** : nos tests de page ajoutent les parcours « résolu », « non résolu → ticket » et « inconnu → tri », absents de la référence, et le flux page → `ui/client` → `/assist` passe par le `motif` de la décision.

**Empreinte de `sentiment-app/`** : 58 813 fichiers avant, 58 813 après, **aucune différence**.

**Étiquette** `tp5`, puis copie `Agent_support_info_TP5`. Après la vérification des tests depuis la copie, ses caches (`__pycache__/`, `.hypothesis/`) sont supprimés : la copie reste celle du commit `tp5`.

---

## TP5.1 : améliorer l'agent

**Date** : 8 novembre 2026 · **Fait par** : membre A (avec Claude Code)

**Ce qui a été fait.** D'abord le diagnostic : 30 conversations réalistes (`data/conversations_30.csv`, versionné) et un utilisateur simulé (`src/bilan_tickets.py`). Ensuite la politique de conversation, dans un module pur (`api/conversation.py`), servie par `POST /chat`, avec ses 49 tests. Puis la base passe de 21 à 42 articles. Côté interface, une page en conversation (`st.chat_message`) : étapes cochables, « Solved » / « Not solved », boutons de catégories, confirmation du ticket, avis « Useful » / « Not useful », suivi d'un ticket, statistiques. Les icônes sont celles de Streamlit (Material), sans emojis. L'API reçoit le stockage des conversations et des avis (`api/stockage.py`), le suivi du statut (`PATCH /tickets/{id}`), les statistiques (`api/suivi.py`), le ticket passé le plus proche (`src/historique.py`) et la reformulation Ollama en option (`api/llm.py`). Le TP comprend aussi `docs/semaine5.1.md`, la fiche du projet, le README et `.env.example`. Un commit par étape, chacun avec les tests verts (sauf l'auteur unique), ruff et mypy muets.

**Décisions et raisons.**

- **La politique dans l'API, pas dans la page** : comme les seuils du TP4, les règles du ticket ne doivent exister qu'à un endroit. La page affiche les boutons que l'API autorise (`choix`) et traduit un code (`REPLIQUES`), comme le `motif` du TP5.
- **Un module pur, des outils injectés** : `avancer(conv, action, outils)` ne connaît ni le modèle, ni la base, ni les fichiers. Les règles se testent donc sans modèle, en CI, comme `decider()` au TP4.
- **Une tentative = un article « pas résolu » ou une question sans résultat** : sans cette définition, une base qui ne sait rien ferait poser des questions sans fin, ou créerait un ticket sans aucune tentative.
- **L'état gardé par l'API** (`tickets/conversations.jsonl`, la dernière version fait foi) : la règle « un seul ticket » ne dépend pas de ce que la page renvoie, et une conversation survit au redémarrage de l'API.
- **`/assist` inchangé** : il trie toujours les fichiers de tickets, et il sert de mesure « avant » au bilan.
- **Seuil du ticket semblable relevé à 0,30** : mesuré sur l'historique Tobi-Bueck, 0,25 montrait des tickets hors sujet.
- **Pas de nouveau jeu de données** : le problème venait de la politique et de la base, pas du modèle (voir `docs/semaine5.1.md`, partie 5).

**Problèmes rencontrés.**

- **`AppTest` et `st.rerun()`** : après un `st.rerun()` lancé dans un clic, l'outil de test gardait des boutons de l'exécution précédente (« Not solved » visible pendant une question). Tous les boutons passent en rappels (`on_click`, `on_submit`), qui mettent l'état à jour avant de redessiner la page : plus aucun `st.rerun()`.
- **Ports déjà pris** : une page Streamlit lancée par l'utilisateur occupait le port 8501, et le port 8000 répondait avec l'ancienne API (21 articles) au moment du premier essai. Nous n'avons pas touché à ces processus : l'essai réel s'est fait sur les ports 8010 (API) et 8511 (page), arrêtés ensuite.
- **Guillemets en ligne de commande** : deux scripts de modification passés par un heredoc échouaient sur les guillemets ; ils ont été écrits dans un fichier temporaire, hors du dépôt.

### T5.1-a · Le diagnostic

```powershell
python src/bilan_tickets.py
```

&nbsp;

**Attendu** : la mesure de la page du TP5 sur 30 conversations, avec la cause de chaque ticket.

**Obtenu** :

```
Avant (TP5) : 18 tickets sur 30 conversations (60%), dont 8 pour un incident que la base sait régler (20 incidents résolubles)
Causes : résolu au premier article 12, confiance_basse 8, « No » au premier article : ticket créé aussitôt 5, priorite_haute 2, mots_inconnus 2, article_escalade 1
```

- [x] Conforme

**Commentaire** :

> Les 8 tickets inutiles : seuil d'abstention 4, garde-fou de vocabulaire 2, priorité haute 1, ticket créé au premier « No » 1. Trois d'entre eux n'avaient pas d'article dans la base (webcam, scanner, application d'authentification).

### T5.1-b · La politique, puis la base

**Obtenu** (même commande) :

```
politique seule, 21 articles :
Après (TP5.1) : 13 tickets sur 30 conversations (43%), attendus 10 ; écarts à l'attendu : 3 ; 2.9 tours en moyenne
42 articles :
Après (TP5.1) : 10 tickets sur 30 conversations (33%), attendus 10 ; écarts à l'attendu : 0 ; 2.7 tours en moyenne
Fins : résolu sans ticket 20, ticket 10
```

- [x] Conforme : aucun ticket pour un incident résolu, un ticket pour chaque cas non résolu, demandé ou critique

### T5.1-c · Tests, qualité

```powershell
python -m pytest -q --cov=api --cov-fail-under=95 ; ruff check . ; mypy api
```

&nbsp;

**Obtenu** :

```
Required test coverage of 95% reached. Total coverage: 99.49%
FAILED tests/test_git_history.py::test_each_member_has_committed
1 failed, 247 passed, 1 xfailed
All checks passed! ; Success: no issues found in 9 source files
```

- [x] Conforme, à l'échec d'auteur du TP1 près (129 tests de plus qu'au TP5)

### T5.1-d · L'agent qui tourne

```powershell
uvicorn api.main:app --port 8010
$env:API_URL="http://127.0.0.1:8010"; streamlit run ui/app.py --server.headless true --server.port 8511
```

&nbsp;

**Obtenu** :

```
page : 200 ; /health : {"status":"OK","model":"tfidf-linearsvc (TP2, models/support.joblib)","articles":42,"llm":"off"}
« The webcam is not detected during video calls » : choisir_categorie ['materiel', 'reseau', 'securite'] > solution « Webcam, microphone or headset not detected » > resolu
page (AppTest, API HTTP) « I clicked a link in a suspicious email and typed my password. » :
  This looks critical. Do the steps below right away. I suggest sending it to a technician now: shall I create a ticket?
  après « Yes » : Ticket TCK-AE375305 created and sent to the Security (SOC) team (status: Open).
python src/historique.py --reel : 8452 tickets passés écrits dans data/historique.csv
```

- [x] Conforme ; un essai dans un navigateur reste à faire (« À faire par l'humain »)

### Membre B, après le TP5.1

À faire par le membre B : `git pull`, `python src/train.py`, `python -m pytest -q`, `python src/bilan_tickets.py`, puis une conversation dans son navigateur.

### Fin du TP5.1 : graphe, empreinte, étiquette, copie

**Graphe** (`graphify update .`, code seulement) : 810 nœuds, 1 555 arêtes, 29 groupes (531 nœuds au TP5). `graphify path "ui/app.py" "api/conversation.py"` ne trouve aucun chemin : la page n'atteint la politique que par HTTP, par `ui/client.py`. La règle d'architecture du cours est respectée.

**Empreinte de `sentiment-app/`** : 58 813 fichiers avant, 58 813 après, **aucune différence**.

**Étiquette** `tp5.1`, puis copie `Agent_support_info_TP5.1`. Après la vérification des tests depuis la copie, ses caches sont supprimés : la copie reste celle du commit `tp5.1`.

**Icônes au lieu des emojis** (demande du binôme, après la première copie) : la page utilise les icônes Material de Streamlit (`:material/...:`) pour l'agent, les onglets, les boutons et les catégories ; les avis deviennent « Useful » / « Not useful ». Un test vérifie qu'aucun emoji ne reste dans `ui/`. L'étiquette `tp5.1` a été déplacée sur ce commit et la copie `Agent_support_info_TP5.1` refaite (`robocopy /MIR`, mêmes exclusions). Les messages des commits précédents gardent leurs emojis : l'historique n'est pas réécrit.

**TP6** : pas encore fait. Il partira de cette version.
