# Agent_support_info : agent de support informatique de premier niveau

Projet du binôme pour le cours *Développement et déploiement d'applications intelligentes* (sujet 9 de la liste des projets).
Un employé décrit un incident informatique dans une conversation ; l'agent le **classe**, cherche une **solution** dans la base de connaissances, la **propose pas à pas** et demande si le problème est **résolu**. Sinon, il propose une autre solution ou pose une question de précision. Il ne propose un **ticket pré-rempli** qu'après deux tentatives sans succès, sur demande, ou pour un cas critique, et ne le crée qu'après confirmation (TP5.1).

Le projet suit la même architecture et la même méthode que `sentiment-app`, TP par TP (TP1 à TP6). Pas de LLM dans les TP1 à TP6 : TF-IDF, modèle linéaire, recherche TF-IDF et règles. Au TP5.1, un LLM local (Ollama) peut reformuler l'article trouvé, en option, désactivé par défaut.

## Démarrage rapide

Le `.venv` est **partagé** : il se trouve dans le dossier de travail, à côté du dépôt, et sert aussi aux copies `Agent_support_info_TPn`.

```powershell
cd ..                                   # le dossier de travail, qui contient Agent_support_info/
py -3.11 -m venv .venv                  # une seule fois
.\.venv\Scripts\Activate.ps1
cd Agent_support_info
pip install -r requirements.txt
```

Depuis le dépôt, l'activation s'écrit `..\.venv\Scripts\Activate.ps1`. Le script `scripts\setup.ps1` fait tout cela en une commande (`powershell -ExecutionPolicy Bypass -File scripts\setup.ps1`).

Puis vérifiez :

```powershell
python scripts/check_setup.py    # diagnostic lisible : versions, venv partagé, dossiers, Git, fiches
python -m pytest -q              # les mêmes vérifications, sous forme de tests
```

En fin de TP1, la même commande affiche `38 passed` une fois que les deux membres ont commité.

## Lancer l'agent

```powershell
python src/make_demo.py; python src/train.py      # le modèle de démonstration (ou train.py --reel)
uvicorn api.main:app --port 8000                  # terminal 1 : l'API (doc sur /docs)
streamlit run ui/app.py                           # terminal 2 : la page (Chat, Track a ticket, Statistics, A file of tickets)
python src/bilan_tickets.py                       # le bilan des tickets sur les 30 conversations (TP5.1)
```

En option : `python src/historique.py --reel` construit l'historique Tobi-Bueck (tickets passés et leur réponse), et `$env:SUPPORT_LLM="ollama"` active la reformulation par Ollama (voir `.env.example`).

## Par où commencer

| Fichier | Contenu |
| --- | --- |
| `docs/cadrage/fiche-cadrage-projet.md` | Le cadrage du projet : besoin, données, métriques, architecture visée |
| `docs/cadrage/cas*.md` | Les trois fiches du TP1 : escalade, classement, solutions |
| `docs/semaine1.md` … | Le compte rendu de chaque TP (`docs/semaine5.1.md` : la conversation et la politique des tickets) |
| `docs/journal.md` | Le journal de bord : ce qui a été fait, les décisions, les contrôles, ce qui reste à faire |
| `TESTS.md` | La démarche de test et les états de référence |
| `AIDE-GIT.md`, `DEPANNAGE.md` | Les commandes Git, et les blocages connus avec leur solution |

## Structure

```text
Agent_support_info/
├── README.md, TESTS.md, AIDE-GIT.md, DEPANNAGE.md
├── Makefile              # raccourcis (optionnel)
├── requirements.txt      # dépendances du semestre, versions figées
├── requirements.lock     # versions exactes installées sur le poste du membre A
├── .gitignore, .env.example, .editorconfig, pytest.ini
├── .vscode/              # interpréteur (../.venv) et tests préconfigurés
├── data/                 # données ; seul exemples_incidents.csv est versionné
├── models/               # modèles entraînés (jamais dans Git)
├── app/                  # prévu au TP1 ; l'API vivra dans api/ (TP3)
├── ui/                   # interface Streamlit (TP5)
├── tests/                # pytest : 23 + 12 + 3 = 38 tests au TP1
├── scripts/              # setup, diagnostic, nouvelle fiche, init du dépôt, clone de vérification
└── docs/                 # cadrage, comptes rendus, journal
```

## Membres du binôme

| Rôle | Nom | Identifiant GitHub | Travail du TP1 |
| --- | --- | --- | --- |
| Membre A | Aadoud Anass | anass0031 | Environnement, structure, fiches, dépôt |
| Membre B | *à compléter par le membre B* | | |
