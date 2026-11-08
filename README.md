# Agent_support_info : agent de support informatique de premier niveau

Projet du binôme pour le cours *Développement et déploiement d'applications intelligentes* (sujet 9 de la liste des projets).
Un employé décrit un incident informatique ; l'application le **classe**, cherche une **solution** dans la base de connaissances, la **propose pas à pas**, demande si le problème est **résolu**, et sinon (ou si le modèle doute, ou si c'est urgent) **crée un ticket pré-rempli** et l'**escalade**.

Le projet suit la même architecture et la même méthode que `sentiment-app`, TP par TP (TP1 à TP6). Pas de LLM dans les TP1 à TP6 : TF-IDF, modèle linéaire, recherche TF-IDF et règles.

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

## Par où commencer

| Fichier | Contenu |
| --- | --- |
| `docs/cadrage/fiche-cadrage-projet.md` | Le cadrage du projet : besoin, données, métriques, architecture visée |
| `docs/cadrage/cas*.md` | Les trois fiches du TP1 : escalade, classement, solutions |
| `docs/semaine1.md` … | Le compte rendu de chaque TP |
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
