# Semaine 3 : l'API, notes du binôme

## Ce que l'API expose

| Route | Rôle | Réponse |
| --- | --- | --- |
| `GET /` | Accueil | liens vers `/docs` et `/health` |
| `GET /health` | Le service est-il prêt ? | 200 : modèle et nombre d'articles ; 503 sans modèle |
| `POST /predict` | Classer un incident | catégorie, confiance, priorité, aperçu du texte |
| `POST /assist` | Proposer une solution ou escalader | le classement, l'article proposé avec ses étapes, la décision (`solution` ou `escalade`), sa raison et le groupe |
| `POST /tickets` | Créer un ticket pré-rempli | **201** ; catégorie et priorité recalculées si absentes, groupe déduit de la catégorie |
| `GET /tickets/{id}` | Relire un ticket | 200, ou **404** s'il n'existe pas |

Les tickets sont écrits dans `tickets/tickets.jsonl`, hors de Git ; la variable `SUPPORT_TICKETS` change ce chemin (les tests écrivent dans un dossier temporaire). Les règles d'escalade de la fiche `cas1` sont dans `api/model.py` (`decider`), dans l'ordre : priorité haute → escalade ; aucun article assez proche → escalade ; article qui demande toujours un technicien (sécurité d'un compte, remboursement, panne) → escalade ; sinon, solution.

## Mesures (modèle de démonstration)

| Contrôle | Essai | Obtenu |
| --- | --- | --- |
| T14 | `python -m pytest -q` | 51 passed, 1 failed (l'auteur unique du TP1) |
| T15 | `GET /health` | 200, `{"status": "OK", "model": "tfidf-linearsvc (TP2, models/support.joblib)", "articles": 21}` |
| T16 | « My VPN keeps disconnecting every 10 minutes when I work from home » | 200, `reseau`, 0,9133, `medium` |
| T17 | « I was charged twice for my subscription this month » | 200, `facturation`, 0,8348, `high` |
| T18 | `{"text": ""}`, `{}`, `{"text": 42}` | 422, 422, 422 |
| T20 | `uvicorn api.main:app` sans `models/support.joblib` | `FileNotFoundError: models/support.joblib absent : lancez python src/train.py`, puis `Application startup failed` |

Le modèle de démonstration donne `high` à « I was charged twice for my subscription this month » : sa priorité est apprise sur les mots d'urgence fixes du générateur, et elle ne vaut rien sur une phrase écrite autrement. C'est la raison pour laquelle la priorité ne sert que dans un sens (forcer une escalade), et pourquoi il faudra la mesurer sur le jeu réel (0,661 au TP2).

## 1. Pourquoi l'API refuse-t-elle de démarrer sans `models/support.joblib`, plutôt que de démarrer et de répondre 503 ?

Nous avons renommé `models/support.joblib` en `support.bak` puis lancé `uvicorn api.main:app`. Le `lifespan` appelle `load_model()`, qui appelle `charger_modele()`, et le démarrage s'arrête sur `FileNotFoundError: models/support.joblib absent : lancez python src/train.py`, suivi de `Application startup failed. Exiting.` Une API sans modèle ne pourrait répondre correctement à aucune requête. Si elle démarrait quand même, un outil de déploiement la croirait en service et les utilisateurs recevraient des 503 au lieu d'une erreur visible tout de suite. Le refus de démarrer rend la panne visible au moment du déploiement. Le 503 sert à autre chose : une indisponibilité passagère pendant que l'API tourne (le modèle retiré en mémoire, vérifié au TP4). La base de connaissances suit la même règle : `charger_base()` est appelée au démarrage et lève `FileNotFoundError` si `data/base_connaissances.csv` manque.

## 2. Un texte vide est refusé deux fois : par Pydantic, puis par `predict()`. Est-ce redondant ?

Les deux refus ne protègent pas la même chose. Pydantic (`min_length=1` dans `PredictRequest`) refuse `""` avant même d'appeler la fonction de la route, avec un 422 dont le `detail` est une liste d'erreurs normalisée. `predict()` refuse aussi les textes faits d'espaces, et il protège les appelants qui ne passent pas par l'API : la ligne de commande, les scripts, la future commande `support`. Nous avons observé la limite de ce double refus : `{"text": "   "}` passe le contrat, puis `predict()` lève `ValueError`, que la route traduit en `422 {"detail": "texte vide"}`, une simple chaîne. Le même refus a donc deux formes selon le texte. C'est le premier défaut que le TP4 doit corriger, en mettant la règle des espaces dans le schéma.

## Ce qui n'est pas fait au TP3

La réponse du ticket passé le plus proche (colonne `answer` de Tobi-Bueck), possible d'après le cadrage, n'est pas exposée : elle demanderait de charger le jeu réel dans l'API, alors que l'API de la CI tourne sur le modèle de démonstration, sans réseau. L'abstention (`INDETERMINE`) vient au TP4, comme dans le cours.
