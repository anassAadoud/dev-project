# Semaine 5.1 : un agent qui répond avant de créer un ticket, notes du binôme

> Étape ajoutée entre le TP5 et le TP6 : améliorer l'agent sans changer son architecture
> (page → `ui/client.py` → HTTP → API → modèle + base de connaissances). Chiffres mesurés sur le
> modèle de démonstration (`models/metrics.json`, F1 macro 0,856, inchangé : le modèle n'a pas été réentraîné).

## Ce qui a changé, et pourquoi

| Avant (TP5) | Après (TP5.1) | Pourquoi |
| --- | --- | --- |
| Une question, une réponse (`/assist`), puis « Is it solved? » | Une conversation à plusieurs tours (`POST /chat`), gardée par l'API | L'agent doit pouvoir proposer une autre solution et poser une question |
| Ticket proposé dès que le modèle hésite, que la priorité est haute ou qu'aucun article ne correspond | Jamais de ticket au premier message | 8 tickets sur 20 incidents résolubles étaient inutiles (diagnostic ci-dessous) |
| « No » créait le ticket aussitôt | Une autre solution ou une question de précision ; le ticket après **2 tentatives** sans succès | Un article raté n'est pas un incident insoluble |
| Modèle hésitant : « I don't know », ticket pour le tri | Question de précision avec les **boutons de catégories**, classés par proximité avec la base | L'utilisateur sait souvent de quoi il s'agit, le modèle de démonstration non |
| Ticket créé sans confirmation pour une escalade | Ticket toujours **confirmé** par l'utilisateur, même pour un cas critique | Le ticket est un engagement de l'équipe : l'utilisateur doit le vouloir |
| Plusieurs tickets possibles pour un même incident | **Un seul ticket par conversation** (refusé en 409 sinon) | Pas de doublons pour les techniciens |
| Ticket : texte, catégorie, article | Ticket pré-rempli : **résumé**, catégorie, priorité, **articles essayés et étapes cochées**, raison | Le technicien ne repose pas les questions déjà posées |
| 21 articles (3 par catégorie) | **42 articles** (6 par catégorie) | Webcam, scanner, double authentification… manquaient (3 des 8 tickets inutiles) |
| Statut figé « ouvert » | Suivi : ouvert, en cours, résolu, fermé, avec historique (`PATCH /tickets/{id}`) | L'utilisateur suit son ticket, le technicien le fait avancer |
| — | Avis 👍/👎 par réponse (`POST /feedback`), statistiques (`GET /stats`) | Mesurer l'agent en usage : taux de résolution sans ticket, catégories fréquentes |
| — | Ticket passé le plus semblable et ce qui l'a réglé | Réutiliser les résolutions des techniciens |
| Pas de LLM | Reformulation par Ollama **en option**, désactivée par défaut | Une réponse plus naturelle, sans rendre l'agent dépendant d'un LLM |

`/assist` et ses règles (fiche `cas1`) restent ceux du TP4 : ils servent toujours au tri d'un fichier de tickets (onglet « A file of tickets »).

## 1. Le diagnostic : pourquoi l'agent créait trop de tickets

`data/conversations_30.csv` contient 30 incidents réalistes, écrits pour ce diagnostic, avec l'utilisateur qui les écrit : 20 que la base sait régler (`resolu`, avec les articles qui les règlent), 4 qu'aucun article ne règle (`non_resolu`), 3 où l'utilisateur veut un technicien (`demande`), 3 cas critiques (`critique`). Un utilisateur simulé (`src/bilan_tickets.py`) répond à l'agent : « résolu » si l'article proposé est l'un des siens, « pas résolu » sinon, sa phrase de précision si on lui pose une question, la bonne catégorie si on lui montre les boutons, « oui » si on lui propose un ticket.

Mesure de la page du TP5 (une escalade de `/assist` mène au ticket, « No » le crée aussitôt) :

```
Avant (TP5) : 18 tickets sur 30 conversations (60%), dont 8 pour un incident que la base sait régler (20 incidents résolubles)
Causes : résolu au premier article 12, confiance_basse 8, « No » au premier article : ticket créé aussitôt 5, priorite_haute 2, mots_inconnus 2, article_escalade 1
```

Les **8 tickets inutiles**, par cause :

| Cause | Tickets inutiles | Exemples |
| --- | --- | --- |
| Seuil d'abstention (confiance sous 0,60) | 4 | « I typed my password wrong a few times and now my account is locked » (0,56) ; « A colleague can't get into the CRM » (0,44) |
| Garde-fou de vocabulaire (moins de 50 % de mots connus) | 2 | « The scanner produces blank pages » (40 %) ; « It's not working again, same as last week » (38 %) |
| Priorité haute | 1 | « I never received the receipt for last month's payment » (priorité `high` prédite) |
| Création automatique au premier « No » | 1 | « My authenticator app stopped working after I changed phones » (classé `logiciel`, mauvais article) |
| Article absent de la base (cause sous-jacente) | 3 des 8 | webcam, scanner, application d'authentification |

Le modèle de démonstration a un petit vocabulaire (36 symptômes synthétiques) : il hésite sur beaucoup de phrases réelles. Au TP5, chaque hésitation devenait un ticket. Le seuil d'abstention est juste (il évite les erreurs franches, TP4), mais la réponse à l'hésitation était mauvaise : un ticket, au lieu d'une question.

## 2. La nouvelle politique

Elle est dans `api/conversation.py`, un module pur : il ne connaît ni le modèle, ni la base, ni les fichiers, qui lui sont passés en `outils`. Les tests la fixent donc sans modèle (49 tests dans `tests/test_conversation.py`, CI comprise).

1. **Premier message** : l'agent classe le texte, cherche un article et propose ses étapes. Aucun ticket n'est créé, quel que soit le cas (testé sur huit cas : simple, priorité haute, hésitation, mots inconnus, sécurité, panne, demande explicite, sans article).
2. **Modèle hésitant** (`INDETERMINE`) : question de précision et boutons de catégories (`choisir_categorie`), ou demande de reformuler en anglais si la plupart des mots sont inconnus (`reformuler`). Les boutons sont classés par la proximité du texte avec les articles de chaque catégorie (`categories_proches` dans `src/kb.py`).
3. **Pas résolu** : un autre article de la catégorie, jamais un déjà essayé (`chercher(..., exclus=...)`). S'il n'y en a plus : une question de précision (`question_precision`). La réponse de l'utilisateur complète le texte, et le modèle relit le tout.
4. **Une tentative sans succès** est un article « pas résolu », ou une question de précision qui n'a mené à aucun article. Après **2 tentatives** (`MAX_TENTATIVES`), l'agent propose le ticket (`deux_essais`).
5. Le ticket est aussi proposé si l'utilisateur le **demande** (bouton « Ask for a technician », ou ses mots : « please open a ticket », « I need a technician », « talk to a human »), ou pour un **cas critique** (`securite`, `panne_service`) : dans ce cas, les étapes de l'article restent affichées, pour agir en attendant.
6. **Confirmation** : le ticket n'est créé qu'avec l'action `confirmer_ticket`. « Not now » rend la main à l'agent.
7. **Un seul ticket par conversation** : un second `confirmer_ticket` répond 409, et `POST /tickets` avec le même `conversation_id` aussi.

La priorité haute ne déclenche plus d'escalade : elle reste affichée et passe dans le ticket.

## 3. Mesures avant/après sur les 30 conversations

```
python src/bilan_tickets.py
```

| Mesure | Avant (TP5) | Politique seule (21 articles) | Après (TP5.1, 42 articles) |
| --- | --- | --- | --- |
| Tickets créés | **18 / 30 (60 %)** | 13 / 30 (43 %) | **10 / 30 (33 %)** |
| Tickets attendus (non résolu, demande, critique) | 10 | 10 | 10 |
| Tickets pour un incident que la base sait régler | **8 / 20** | 3 / 20 | **0 / 20** |
| Incidents non résolus, demandés ou critiques sans ticket | 0 / 10 | 0 / 10 | 0 / 10 |
| Ticket au premier message | possible | 0 | 0 |
| Plus d'un ticket par conversation | possible | 0 | 0 |
| Tours par conversation (moyenne) | 1 à 2 | 2,9 | 2,7 |

Les 3 écarts de la colonne du milieu (webcam, application d'authentification, scanner) venaient d'articles absents : l'agent a fait deux tentatives, puis proposé le ticket. C'est le comportement voulu quand la base ne sait pas, et c'est ce qui a montré quels articles écrire. Dans la version finale, 6 conversations sur 30 passent par un second article (`autre_solution`), et 9 par une question ou par les boutons.

`tests/test_bilan_tickets.py` rejoue les 30 conversations à chaque `pytest` (32 tests) : aucun ticket pour un incident résolu dont l'article est dans la base, un ticket pour chacun des autres, jamais au premier message. Un autre test vérifie que chaque article attendu existe dans la base.

## 4. Le chatbot

- **Conversation** : `st.chat_message` et `st.chat_input`, fil gardé dans `st.session_state`, et état complet gardé par l'API (`tickets/conversations.jsonl`) : une conversation survit au redémarrage de l'API (testé). Les boutons sont ceux que l'API autorise (champ `choix`), en rappels `on_click`.
- **Étapes cochables**, boutons « ✅ Solved » / « ❌ Not solved » : les étapes cochées passent dans le ticket.
- **Base de connaissances** : 42 articles, 6 par catégorie (testé : au moins 5, identifiants uniques, au moins 3 étapes).
- **Ticket passé le plus semblable** (`src/historique.py`) : d'abord les tickets de l'agent qu'un technicien a résolus, avec leur résolution, puis l'historique Tobi-Bueck s'il est construit (`python src/historique.py --reel` : 8 452 tickets passés avec la réponse du support, dans `data/historique.csv`, hors Git). Mesure sur les 30 messages : 5 tickets semblables au seuil 0,25, 2 au seuil retenu de 0,30, 68 ms par recherche. Les réponses de Tobi-Bueck sont souvent génériques (« please provide more details… ») et les tickets proches parlent parfois d'autre chose (« billing access denied » pour un dossier partagé) : le seuil a été relevé à 0,30, et la source la plus utile reste les résolutions des techniciens de l'agent.
- **Suivi d'un ticket** (onglet « Track a ticket ») : statut, équipe, résumé, articles déjà essayés, historique ; un formulaire « Technician » fait avancer le statut et saisit la résolution, qui devient un ticket passé semblable pour les incidents suivants.
- **Avis 👍/👎** sur chaque réponse de l'agent, enregistrés avec le code de la réponse (`tickets/feedback.jsonl`).
- **Statistiques** (onglet « Statistics ») : taux de résolution sans ticket (conversations résolues seules, divisées par les conversations terminées), conversations, tickets, avis, et les catégories fréquentes en barres horizontales (une seule série, une seule teinte, avec le tableau des chiffres).
- **Design** : barre latérale (état de l'API, nouvelle conversation, mode d'emploi), icônes par catégorie, pastilles de confiance et de priorité, étapes encadrées.
- **LLM en option** (`api/llm.py`) : si `SUPPORT_LLM=ollama`, l'API demande à Ollama de reformuler l'article trouvé, sans rien ajouter. Désactivé par défaut (`/health` affiche `"llm": "off"`). Toute erreur (Ollama absent, lent, réponse vide) rend `None`, et la page affiche l'article seul. Les tests simulent la réponse d'Ollama : aucun ne l'appelle (un test échoue si l'option désactivée tente un appel).

Nouvelles routes : `POST /chat`, `GET /tickets`, `PATCH /tickets/{id}`, `POST /feedback`, `GET /stats`. Les tickets, conversations et avis sont des fichiers JSON Lines dans le dossier de `SUPPORT_TICKETS` (`api/stockage.py`) : une modification ajoute une version, la dernière fait foi.

## 5. Autres jeux de données

**Aucun nouveau jeu n'a été ajouté.** L'objectif du TP5.1 est atteint sans réentraîner le modèle : les tickets inutiles venaient de la politique (hésitation → ticket) et de la base, pas d'une erreur franche du modèle. Les boutons de catégories compensent les faiblesses du modèle de démonstration sur `compte_acces` et `materiel`. Le seul jeu utilisé est Tobi-Bueck, déjà retenu au TP2, pour l'historique des tickets passés, et il n'est pas versionné. Un jeu public supplémentaire pour les catégories faibles ou les messages courts reste une piste pour améliorer le modèle réel (`train.py --reel`) : il faudra d'abord le valider avec le binôme (lien, licence, taille, correspondance avec nos 7 catégories), et ne le garder que s'il améliore le F1 macro, le rappel par catégorie et le taux de tickets sur les 30 messages.

## Mesures de contrôle

| Contrôle | Obtenu |
| --- | --- |
| `python -m pytest -q` | 246 passed, 1 xfailed, 1 failed (l'auteur unique, comme au TP1) : 128 tests de plus qu'au TP5 |
| Couverture de `api/` | 99 % (592 instructions, 3 non couvertes) ; seuil de la CI : 95 % |
| `ruff check .` ; `mypy api` | All checks passed! ; Success: no issues found in 9 source files |
| API réelle (port 8010) et page (port 8511) | `/health` : 42 articles, `"llm": "off"` ; la page répond 200 |
| Conversation réelle « The webcam is not detected during video calls » | boutons (Hardware en premier), article « Webcam, microphone or headset not detected », « Solved » : aucun ticket, taux 100 % |
| Page réelle (AppTest sur l'API HTTP) : « I clicked a link in a suspicious email and typed my password. » | « This looks critical… shall I create a ticket? » ; après « Yes » : `Ticket TCK-AE375305 created and sent to the Security (SOC) team (status: Open).` |

Un essai à la main dans un navigateur reste à faire (voir le journal).
