**Chapitre 1 : Fondamentaux et cadrage**6 éléments

1 : Définitions, histoire, évolution et applications de l’IA.À traiter

2 : Règles métier, machine learning, deep learning, modèles génératifs et RAG.À traiter

3 : Présentation de TensorFlow, PyTorch et des bibliothèques Python utiles.À traiter

4 : Cycle de vie : données, modèle, API, interface, déploiement et suivi.À traiter

5 : Choix d’une approche, critères d’acceptation, métriques et limites.À traiter

6 : Enjeux éthiques, confidentialité, biais et validation humaine.À traiter

**2Chapitre 2 : Développement d’applications ML et services API**7 éléments

1 : Python, environnements virtuels, dépendances et organisation d’un projet.À traiter

2 : Frameworks web : Flask ou FastAPI comme support principal ; aperçu de Django, Pyramid et Express.À traiter

3 : API REST : endpoints, validation, erreurs, documentation, versionnement, authentification et autorisation.À traiter

4 : Intégration d’un modèle de classification ou de prédiction dans une application.À traiter

5 : Streamlit : interface interactive, visualisation et déploiement d’une démonstration.À traiter

6 : Packaging Python : setuptools, wheel, documentation et tests.À traiter

7 : Intégration complémentaire dans une architecture Java/Spring Boot.À traiter

**3Chapitre 3 : MLOps, DevOps et déploiement**7 éléments

1 : DevOps et MLOps : principes, différences, cycle de vie logiciel, données et modèles.À traiter

2 : MLflow : suivi des expériences, paramètres, métriques, modèles et artefacts.À traiter

3 : DVC : versionnement des jeux de données et reproductibilité des expériences.À traiter

4 : Docker et Docker Compose : image, service, configuration et environnement reproductible.À traiter

5 : CI/CD simplifié : tests, construction et déploiement automatisé.À traiter

6 : Introduction à Kubeflow Pipelines ou Azure Machine Learning comme plateformes d’orchestration.À traiter

7 : Déploiement, logs, monitoring, latence, coût et gestion des erreurs.À traiter

**4Chapitre 4 : RAG et intégration des modèles génératifs**5 éléments

1 : Appel d’un modèle de langage par API ou modèle à poids ouverts.À traiter

2 : Prompts structurés, sorties JSON et validation des réponses.À traiter

3 : Embeddings, recherche sémantique, index vectoriel et métadonnées.À traiter

4 : RAG : ingestion, découpage, indexation, recherche, génération et citations.À traiter

5 : Évaluation, hallucinations, injection de prompt et confidentialité.À traiter

**5Chapitre 5 : Sécurité, évaluation et projet intégrateur**5 éléments

1 : Authentification, autorisation, secrets, contrôle d’accès et protection des données.À traiter

2 : Tests fonctionnels, tests d’API, qualité des sorties et gestion des erreurs.À traiter

3 : Évaluation : précision, rappel, F1 ou métriques adaptées ; pour le RAG, pertinence et fidélité.À traiter

4 : Explicabilité avec LIME ou SHAP en introduction, lorsque le type de modèle le permet.À traiter

5 : Documentation de l’architecture, des données, des modèles, des limites et des conditions d’usage.À traiter

**6Travaux pratiques Liste minimale des travaux pratiques**8 éléments

TP 1 : Développer une application Flask ou FastAPI pour déployer un modèle de prédiction.À traiter

TP 2 : Créer une API de classification consommée par une application web ou mobile.À traiter

TP 3 : Réaliser une application Streamlit d’analyse et de visualisation de données.À traiter

TP 4 : Développer un package Python de prédiction de sentiment avec setuptools, wheel et tests.À traiter

TP 5 : Mettre en place une expérience MLflow et versionner les données avec DVC.À traiter

TP 6 : Conteneuriser l’API et la déployer avec Docker Compose.À traiter

TP 7 : Construire un mini-RAG documentaire avec réponses référencées.À traiter

TP 8 : Présenter un workflow Kubeflow ou Azure ML et discuter son intérêt par rapport à MLflow.À traiter

&nbsp;

&nbsp;

---

# Notre projet : Agent de support informatique (sujet 9)

> **Ajouté au TP1 (8 novembre 2026).** Tout ce qui précède est notre version initiale de la fiche, gardée telle quelle : le programme du cours. Ce qui suit cadre le projet. Quand un choix change en cours de route (données, catégories, seuils), la rubrique est mise à jour et le changement est signalé dans « Historique des changements », en bas de la fiche.

**Sujet 9** de `projets-agents-ia.xlsx` : *Agent de support informatique*, catégorie Support et ITSM, niveau intermédiaire. Objectif : offrir un premier niveau de support automatisé aux utilisateurs. Fonctionnalités minimales : répondre aux problèmes des utilisateurs, consulter une base de connaissances, proposer des solutions, créer un ticket si nécessaire, escalader les cas complexes. Priorité aux **incidents IT**.

## Besoin en une phrase

Un employé décrit un incident informatique en anglais ; l'application le classe, propose une solution pas à pas tirée de la base de connaissances, demande si le problème est résolu, et sinon (ou si le modèle doute, ou si c'est urgent) crée un ticket pré-rempli et l'escalade au bon groupe de techniciens.

**Mis à jour au TP5.1** : l'agent converse. Il répond d'abord, propose une autre solution ou pose une question de précision quand ce n'est pas résolu ou quand le modèle doute, et ne propose le ticket pré-rempli qu'après deux tentatives sans succès, sur demande, ou pour un cas critique (sécurité, panne générale), toujours après confirmation, un seul par conversation.

## Utilisateur final

Les employés d'une organisation qui rencontrent un incident (poste, réseau, compte, logiciel) ; les techniciens de niveau 1 et 2, qui reçoivent des tickets déjà qualifiés ; le responsable du support, qui maintient la base de connaissances et les règles d'escalade.

## Approche retenue

Le projet combine trois approches, une par décision, cadrées chacune dans une fiche du TP1 :

| Décision | Approche | Fiche |
| --- | --- | --- |
| Classer l'incident (7 catégories IT) et estimer sa priorité | Machine learning : TF-IDF + LinearSVC calibré | `cas2-classement-incidents.md` |
| Proposer une solution pas à pas | RAG réduit à la recherche : similarité TF-IDF dans la base de connaissances, sans génération | `cas3-solutions-base-connaissances.md` |
| Escalader ou non, vers quel groupe | Règles métier | `cas1-escalade-incidents.md` |

**Pas de LLM ni d'Ollama dans les TP1 à TP6.** **Mis à jour au TP5.1** : un LLM local (Ollama) est permis en option, désactivé par défaut, pour reformuler l'article trouvé ; aucune décision ni aucun test n'en dépend.

## Justification

(a) Des incidents étiquetés existent (Tobi-Bueck, catégories tirées des tags), d'où le machine learning pour le classement ; il n'en existe pas pour l'escalade, d'où des règles. (b) Chaque décision doit être vérifiable : une solution cite son article, une escalade donne sa raison. (c) TF-IDF et règles coûtent presque rien par requête, sans GPU. (d) Une erreur coûte du temps à l'utilisateur, ou laisse un incident urgent sans technicien : d'où l'abstention (`INDETERMINE`) et l'escalade par défaut dans le doute.

## Données nécessaires et leur origine

- **Jeu réel** : `Tobi-Bueck/customer-support-tickets` (Hugging Face, CC BY-NC 4.0, tickets fictifs). Filtres : `language == "en"`, `type == "Incident"`, texte = `subject + " " + body`, doublons retirés : 9 179 incidents (notebook `tobi_bueck_incidents_v3.ipynb`, section 4).
- **Étiquette** : la catégorie IT tirée des `tag_*`, première règle qui correspond (section 15.2), identifiants ASCII `securite`, `reseau`, `materiel`, `compte_acces`, `facturation`, `logiciel`, `panne_service` ; les 913 incidents sans catégorie sont écartés, il en reste 8 266 dans le notebook. **Mis à jour au TP2** : `src/train.py --reel` n'applique pas le filtre du notebook sur les queues rares (`MIN_PAR_QUEUE`, 252 tickets), qui ne fait pas partie des filtres retenus ; il garde donc **8 452** incidents étiquetés.
- **Priorité** : la colonne `priority` (low / medium / high), pour un second modèle (section 9).
- **Jeu de démonstration** : `src/make_demo.py` génère un jeu synthétique anglais avec les mêmes 7 catégories, pour la CI et les tests (rapide, sans réseau), comme le jeu de démonstration d'avis dans `sentiment-app`. **Mis à jour au TP5.1** : il reprend aussi le titre et les symptômes des articles de la base (805 incidents, vocabulaire de 1 400 mots au lieu de 661).
- **Jeu d'évaluation (TP5.1)** : `data/jeu_evaluation.csv`, 94 messages (12 par catégorie, 10 hors sujet) jamais utilisés pour écrire la base ni le jeu de démonstration.
- **Base de connaissances** : `data/base_connaissances.csv`, en anglais, au moins 3 articles par catégorie, rédigée par le binôme. **Mis à jour au TP5.1** : au moins 5 articles par catégorie (42 articles, 6 par catégorie).
- **Tickets passés (TP5.1)** : les tickets de l'agent résolus par un technicien et, en option, la réponse (`answer`) des incidents Tobi-Bueck (`python src/historique.py --reel`, 8 452 tickets, hors Git).

## Métrique de succès

| Mesure | Référence du notebook | Seuil d'acceptation |
| --- | --- | --- |
| F1 macro, 7 catégories, Tobi-Bueck | 0,788 (LinearSVC calibré) ; naïf 0,072 | au moins 0,75 ; le 0,85 du cours n'est pas atteint sur données réelles, c'est documenté |
| F1 macro, jeu de démonstration | à mesurer au TP2 | au moins 0,85 (seuil du cours) ; mesuré 0,856 au TP2, 0,907 au TP5.1 |
| Jeu d'évaluation, 94 messages (TP5.1) | 40 justes, 5 faux au TP5 | au moins 58 justes, au plus 6 faux, au plus 1 hors sujet classé (mesuré : 62, 5, 9 sur 10 ; de 55 à 62 justes selon la graine du jeu de démonstration) |
| Priorité exacte, `exemple_test_2.csv` (455 messages, TP5.1) | 43 % | mesurée et rapportée (63 %) ; la priorité seule ne déclenche plus d'escalade |
| Les 2 pièges des 12 incidents (français, charabia) | `INDETERMINE` par le garde-fou de vocabulaire | `INDETERMINE` |
| Tickets sur les 30 conversations du bilan (TP5.1) | 18 / 30 au TP5, dont 8 évitables | aucun ticket pour un incident que la base sait régler, un pour chacun des autres (mesuré : 10 / 30) |
| F1 macro de la priorité | 0,646 ; rappel `high` 0,704 | mesuré et rapporté ; la priorité seule ne décide pas d'une non-escalade |

## Conséquence d'une erreur et validation humaine

Une mauvaise catégorie propose une solution inadaptée : l'utilisateur répond « non résolu » et un ticket part vers un technicien. Une escalade manquée est l'erreur la plus coûteuse : dans le doute (confiance basse, mots inconnus, priorité haute), on escalade. Le technicien peut réaffecter le ticket et corriger la catégorie.

**Mis à jour au TP5.1** : la priorité haute seule ne déclenche plus d'escalade, ni dans la conversation ni dans le fichier de tickets (`decider_tp51`) ; le doute ne crée plus de ticket d'emblée, il déclenche une question (boutons de catégories). L'escalade reste garantie : les cas critiques reçoivent la proposition de ticket dès le premier message, l'utilisateur peut demander un technicien à tout moment, et deux tentatives sans succès mènent au ticket.

## Risques éthiques ou de confidentialité

Données d'entraînement fictives et publiques (licence non commerciale). Les incidents saisis peuvent contenir des données personnelles : tickets stockés hors de Git (`tickets/`), aucun envoi à un service tiers, aucune demande de mot de passe dans les procédures. Le modèle ne comprend que l'anglais : les autres langues doivent aboutir à `INDETERMINE`, donc à un humain. Données publiques, fictives ou anonymisées uniquement (RGPD, loi 09-08).

## Seuils et paramètres de départ

| Paramètre | Valeur de départ | Où il sera mesuré |
| --- | --- | --- |
| `SEUIL_ABSTENTION` | 0,5 ; **0,60 depuis le TP4** (mesuré, voir `docs/semaine4.md`) | `src/courbe_seuil.py` (TP4) |
| Garde-fou de vocabulaire | `INDETERMINE` si moins de 50 % des mots sont connus du modèle ; **sans compter les mots vides depuis le TP5.1** | notebook, section 15.1 ; TP4 ; `src/bilan_evaluation.py` (TP5.1) |
| `SEUIL_BASE` (TP5.1) | 0,25 : le second avis de la base quand le modèle hésite | `src/bilan_evaluation.py`, jeu d'évaluation et 50 messages de développement |
| Découpage | 80 / 20 stratifié, graine 42, **avant** la vectorisation | `src/train.py` (TP2) |
| Modèle | TF-IDF (1-2 grammes, `min_df=2`, `sublinear_tf`) + `LinearSVC` calibré, `class_weight="balanced"` | `src/train.py` (TP2) |

## Architecture visée (identique à sentiment-app)

`ui/app.py → ui/client.py → HTTP → api/main.py → api/model.py → src/predict.py + src/kb.py → models/ + data/`

Routes prévues : `GET /`, `GET /health`, `POST /predict`, `POST /assist`, `POST /tickets` (201), `GET /tickets/{id}` (404 si absent). **Ajoutées au TP5.1** : `POST /chat` (la conversation), `GET /tickets`, `PATCH /tickets/{id}` (suivi du statut), `POST /feedback` (avis utile ou pas), `GET /stats`. La politique de conversation vit dans `api/conversation.py`.

## Historique des changements

| Date | TP | Changement |
| --- | --- | --- |
| 2026-11-08 | TP1 | Cadrage du projet ajouté sous la version initiale ; trois fiches `cas*.md` |
| 2026-11-08 | TP2 | Données réelles : 8 452 incidents étiquetés (pas de filtre sur les queues rares) ; F1 macro mesuré 0,789 sur Tobi-Bueck, 0,856 sur la démonstration ; priorité : F1 0,661, rappel `high` 0,717 |
| 2026-11-08 | TP3 | Base de connaissances écrite : 21 articles (3 par catégorie) ; seuil de similarité 0,10 ; routes `/assist` et `/tickets` en place ; la réponse du ticket passé n'est pas exposée |
| 2026-11-08 | TP4 | `SEUIL_ABSTENTION` passe de 0,5 à 0,60 (courbe du seuil sur la démonstration et sur Tobi-Bueck) ; garde-fou de vocabulaire branché dans l'API ; `INDETERMINE` → groupe « Tri N1 » |
| 2026-11-08 | TP5 | Page Streamlit en anglais ; `/assist` renvoie un `motif` ; groupes d'escalade renommés en anglais (Triage (L1) pour les incidents incertains) |
| 2026-11-08 | TP5.1 | Politique des tickets : jamais au premier message, deux tentatives, confirmation, un seul par conversation (18 → 10 tickets sur 30 conversations) ; base de 42 articles ; conversation multi-tours, suivi, avis, statistiques, ticket passé le plus proche ; Ollama en option, désactivé par défaut ; aucun nouveau jeu de données |
| 2026-11-08 | TP5.1 | Qualité : jeu de démonstration enrichi par la base (F1 0,924), second avis de la base (`SEUIL_BASE` 0,25), garde-fou sans mots vides ; jeu d'évaluation de 94 messages : 40 → 63 justes, 5 faux, hors sujet 10 sur 10 ; fichier de 1 000 tickets : 63 % → 34 % d'INDETERMINE |
| 2026-11-08 | TP5.1 | Priorité du jeu de démonstration : urgence → high, calme (négations comprises) → low, sinon selon la catégorie ; graine du jeu choisie sur les 50 messages de développement (2) ; `/assist` suit la conversation (`decider_tp51`) : 387 → 293 escalades sur 500 messages ; priorité exacte 43 % → 63 % |
