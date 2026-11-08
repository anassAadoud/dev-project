# Semaine 1 : cadrer l'application et préparer l'environnement

`sentiment-app` n'a pas de `semaine1.md` : le TP1 y est documenté par les fiches `docs/cadrage/cas*.md`. Ce compte rendu suit l'énoncé du TP1 (`TP1-ENONCE.md`) : objectifs, partie A (cadrage), partie B (environnement et dépôt), livrables et grille, appliqués à notre sujet.

## Objectifs du TP1, appliqués à notre projet

1. Trois fiches de cadrage argumentées : ici, une par décision de notre agent (`docs/cadrage/cas1-escalade-incidents.md`, `cas2-classement-incidents.md`, `cas3-solutions-base-connaissances.md`), plus la fiche du projet complétée (`docs/cadrage/fiche-cadrage-projet.md`).
2. Un dépôt Git `Agent_support_info`, structuré comme `sentiment-app`, où les deux membres ont commité (le dépôt GitHub et le commit du membre B sont à faire par un humain).
3. Un environnement Python reproductible, vérifié par `python scripts/check_setup.py` et par `pytest` : ici un `.venv` Python 3.11 **partagé**, dans le dossier de travail.

## Partie A : le cadrage

La grille du cours (`docs/cadrage/GRILLE-DE-DECISION.md`) pose quatre critères : (a) données étiquetées, (b) vérifiabilité, (c) coût par requête, (d) conséquence d'une erreur. L'arbre de choix a été parcouru pour chacune des trois décisions de l'agent :

| Fiche | Décision | Arbre de choix | Approche | Critères décisifs |
| --- | --- | --- | --- | --- |
| `cas1-escalade-incidents.md` | Escalader ou non, vers quel groupe | 1. La logique est connue, stable, doit rester explicable : oui | Règles métier | (b) une escalade s'explique ; (d) une escalade manquée coûte cher ; (a) aucun historique d'escalades |
| `cas2-classement-incidents.md` | Catégorie IT de l'incident | 1. non (formulations trop variées) ; 2. données étiquetées pour une tâche répétitive : oui | Machine learning | (a) 8 266 incidents étiquetés par les tags ; (c) coût quasi nul ; (d) erreur limitée par l'abstention |
| `cas3-solutions-base-connaissances.md` | Quelle procédure proposer | 1. non ; 2. non (pas de paires question-réponse) ; 3. réponse tirée de documents et citée : oui | RAG (recherche seule, sans génération aux TP1-6) | (b) article cité ; (a) documents mais pas d'étiquettes ; (d) jamais de procédure inventée |

Ce découpage a une conséquence pour la suite : le projet n'est pas « un modèle », mais un modèle (TP2), une recherche dans une base (TP3) et des règles (TP3, TP4), réunis derrière une seule API.

**Ce que la fiche du projet a fixé dès le TP1** (rubrique « Seuils et paramètres de départ ») : les données (Tobi-Bueck, anglais, incidents, catégories tirées des tags), le modèle (TF-IDF + LinearSVC calibré), le seuil d'abstention de départ (0,5) et le garde-fou de vocabulaire (50 % de mots connus), tous tirés du notebook `tobi_bueck_incidents_v3.ipynb`.

## Partie B : l'environnement et le dépôt

| Étape de l'énoncé | Chez nous |
| --- | --- |
| B1. Outils système | Python 3.11.9 (à côté de 3.14), Git 2.49 |
| B2. Créer le dépôt GitHub | À faire par le membre A (compte requis) : dépôt privé, membre B en Write, enseignant |
| B3. Initialiser le dépôt | `git init`, premier commit, branche `main`, étiquette `tp1` ; le `push` est à faire par un humain |
| B4. Installer l'environnement | `.venv` partagé dans le dossier de travail ; `scripts/setup.ps1` le crée à `..\.venv` |
| B5. Un commit par membre | Membre A : fait. Membre B : à faire (clone, ligne du README, commit, push) |
| B6. Vérification finale | Voir « Mesures » ci-dessous |

Le choix d'un `.venv` partagé a demandé trois adaptations : `scripts/setup.ps1` et `setup.sh` créent le venv dans le dossier parent ; `scripts/check_setup.py` indique si le venv actif est le venv partagé ou un venv du dépôt (clone frais, CI), et accepte les deux ; les messages des tests et `DEPANNAGE.md` donnent la commande d'activation `..\.venv\Scripts\Activate.ps1`.

## Mesures

| Contrôle | Commande | Obtenu |
| --- | --- | --- |
| T1 (fiches vides) | `python -m pytest -q` | 3 failed, 31 passed, 4 skipped |
| T2 | `python -m pytest tests/test_cadrage.py -q` | 12 passed |
| T3 | `python -m pytest -q`, après `git init` et les commits | 37 passed, 1 failed |
| T4 | `python scripts/check_setup.py` | 0 erreur(s), 1 avertissement(s) |
| T7 | clone frais du dépôt local, `.venv` neuf | 0 erreur(s), 37 passed, 1 failed |

Le seul échec, `test_each_member_has_committed`, et le seul avertissement disent la même chose : le dépôt n'a encore qu'un auteur. Ils disparaissent avec le commit du membre B. Les autres résultats correspondent aux états de référence du guide.

## Livrables

- [x] Trois fiches `docs/cadrage/cas*.md` remplies, plus la fiche du projet complétée
- [ ] `README.md` avec le tableau du binôme complété : ligne du membre A faite, ligne du membre B à ajouter par lui
- [x] `requirements.lock` généré (181 lignes, poste du membre A)
- [x] Structure de dossiers conforme
- [ ] Un commit par membre visible dans `git shortlog -sn` : membre A seulement
- [ ] CI verte sur GitHub : le dépôt GitHub reste à créer

## Ce que le TP1 change pour la suite

Les fiches deviennent le cahier des charges : `cas2` fixe le modèle et les seuils du TP2 (F1 macro, abstention), `cas3` la base de connaissances et la recherche du TP3, `cas1` les règles d'escalade du TP3 et du TP4.
