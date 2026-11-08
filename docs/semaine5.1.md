# Semaine 5.1 : un agent qui répond avant de créer un ticket, notes du binôme

> Étape ajoutée entre le TP5 et le TP6 : améliorer l'agent sans changer son architecture
> (page → `ui/client.py` → HTTP → API → modèle + base de connaissances). Chiffres mesurés sur le
> modèle de démonstration, réentraîné au TP5.1 sur un jeu enrichi (`models/metrics.json`, F1 macro 0,907 au lieu de 0,856, priorité revue : parties 5 et 6).

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
| — | Avis « Useful » / « Not useful » par réponse (`POST /feedback`), statistiques (`GET /stats`) | Mesurer l'agent en usage : taux de résolution sans ticket, catégories fréquentes |
| — | Ticket passé le plus semblable et ce qui l'a réglé | Réutiliser les résolutions des techniciens |
| Pas de LLM | Reformulation par Ollama **en option**, désactivée par défaut | Une réponse plus naturelle, sans rendre l'agent dépendant d'un LLM |

`/assist` et ses règles (fiche `cas1`) restent ceux du TP4 : ils servent toujours au tri d'un fichier de tickets (onglet « A file of tickets »).

## 1. Le diagnostic : pourquoi l'agent créait trop de tickets

`data/conversations_30.csv` contient 30 incidents réalistes, écrits pour ce diagnostic, avec l'utilisateur qui les écrit : 20 que la base sait régler (`resolu`, avec les articles qui les règlent), 4 qu'aucun article ne règle (`non_resolu`), 3 où l'utilisateur veut un technicien (`demande`), 3 cas critiques (`critique`). Un utilisateur simulé (`src/bilan_tickets.py`) répond à l'agent : « résolu » si l'article proposé est l'un des siens, « pas résolu » sinon, sa phrase de précision si on lui pose une question, la bonne catégorie si on lui montre les boutons, « oui » si on lui propose un ticket.

Mesure de la page du TP5 (une escalade de `/assist` mène au ticket, « No » le crée aussitôt), avec le modèle du TP5. `src/bilan_tickets.py` rejoue cette politique avec le modèle courant : depuis le modèle du TP5.1 (partie 5), sa ligne « Avant » affiche 16 tickets, dont 6 évitables :

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
- **Étapes cochables**, boutons « Solved » / « Not solved » : les étapes cochées passent dans le ticket.
- **Base de connaissances** : 42 articles, 6 par catégorie (testé : au moins 5, identifiants uniques, au moins 3 étapes).
- **Ticket passé le plus semblable** (`src/historique.py`) : d'abord les tickets de l'agent qu'un technicien a résolus, avec leur résolution, puis l'historique Tobi-Bueck s'il est construit (`python src/historique.py --reel` : 8 452 tickets passés avec la réponse du support, dans `data/historique.csv`, hors Git). Mesure sur les 30 messages : 5 tickets semblables au seuil 0,25, 2 au seuil retenu de 0,30, 68 ms par recherche. Les réponses de Tobi-Bueck sont souvent génériques (« please provide more details… ») et les tickets proches parlent parfois d'autre chose (« billing access denied » pour un dossier partagé) : le seuil a été relevé à 0,30, et la source la plus utile reste les résolutions des techniciens de l'agent.
- **Suivi d'un ticket** (onglet « Track a ticket ») : statut, équipe, résumé, articles déjà essayés, historique ; un formulaire « Technician » fait avancer le statut et saisit la résolution, qui devient un ticket passé semblable pour les incidents suivants.
- **Avis « Useful » / « Not useful »** sur chaque réponse de l'agent, enregistrés avec le code de la réponse (`tickets/feedback.jsonl`).
- **Statistiques** (onglet « Statistics ») : taux de résolution sans ticket (conversations résolues seules, divisées par les conversations terminées), conversations, tickets, avis, et les catégories fréquentes en barres horizontales (une seule série, une seule teinte, avec le tableau des chiffres).
- **Design** : barre latérale (état de l'API, nouvelle conversation, mode d'emploi), icônes Material de Streamlit (aucun emoji) pour l'agent, les onglets, les boutons et chaque catégorie, pastilles de confiance et de priorité, étapes encadrées.
- **LLM en option** (`api/llm.py`) : si `SUPPORT_LLM=ollama`, l'API demande à Ollama de reformuler l'article trouvé, sans rien ajouter. Désactivé par défaut (`/health` affiche `"llm": "off"`). Toute erreur (Ollama absent, lent, réponse vide) rend `None`, et la page affiche l'article seul. Les tests simulent la réponse d'Ollama : aucun ne l'appelle (un test échoue si l'option désactivée tente un appel).

Nouvelles routes : `POST /chat`, `GET /tickets`, `PATCH /tickets/{id}`, `POST /feedback`, `GET /stats`. Les tickets, conversations et avis sont des fichiers JSON Lines dans le dossier de `SUPPORT_TICKETS` (`api/stockage.py`) : une modification ajoute une version, la dernière fait foi.

## 5. La qualité des réponses : le modèle, la base et le garde-fou

Le fichier de 1 000 tickets du binôme (`results.csv`, page « A file of tickets ») donnait 633 « I don't know » (63 %) et des erreurs franches (« What is the meaning of life? » → Service outage, micro du casque → Security). La politique de conversation compense l'hésitation par une question, mais un fichier de tickets ne peut pas poser de question. La qualité du classement compte donc aussi.

**Mesure honnête d'abord.** `data/jeu_evaluation.csv` : 94 messages écrits avant toute modification, et jamais utilisés pour écrire la base ni le jeu de démonstration (12 par catégorie, 10 hors sujet). `src/bilan_evaluation.py` compte, pour chaque message, « juste » (la bonne catégorie, ou INDETERMINE pour un hors sujet), « faux » (une autre catégorie) ou « hésite » (INDETERMINE pour un vrai incident, qui mène à une question dans la conversation). Les seuils ont été comparés sur ce jeu et sur les 50 messages de développement (`conversations_30.csv` et `jeu_or.csv`) : un choix doit tenir sur les deux.

**Ce qui a été essayé.**

| Essai | Jeu d'évaluation (juste / faux / hésite) | Fichier de 1 000 tickets : INDETERMINE | Retenu ? |
| --- | --- | --- | --- |
| Départ : modèle de démonstration du TP5 (661 mots) | 40 / 5 / 49 | 633 (63 %) | — |
| Modèle réel Tobi-Bueck (`train.py --reel`, 28 420 mots), même seuils | non mesuré sur ce jeu | 572 (57 %), aucun `materiel` | non : entraîné sur de longs courriels, il ne connaît pas les tickets d'une ligne |
| Jeu de démonstration enrichi par les symptômes de la base (805 incidents, 1 400 mots) | 57 / 6 / 31 | 384 (38 %) | oui |
| + second avis de la base quand le modèle hésite (`SEUIL_BASE` 0,25) | 66 / 7 / 21 | 304 (30 %) | oui |
| + garde-fou de vocabulaire sans les mots vides | 60 / 4 / 30, hors sujet 10 sur 10 | 357 (36 %) | oui : moins d'erreurs franches |
| Seuil d'abstention 0,50 ou 0,55 au lieu de 0,60 | jusqu'à 66 / 14 / 14 | — | non : les erreurs franches doublent |
| Second avis limité aux 2 ou 3 catégories préférées du modèle | 59 à 63 / 3 à 4 | 287 à 371 | non : écarts de 1 à 3 messages, du bruit sur des jeux de cette taille |
| + deux symptômes matériels dans la base (souris sans fil, poste qui redémarre avec une clé USB), vus dans le fichier du binôme | **63 / 5 / 26**, hors sujet 10 sur 10 | **343 (34 %)** | oui |

**Les trois changements retenus.**

1. **Le jeu de démonstration parle le vocabulaire de la base** (`src/make_demo.py`) : en plus des 36 symptômes du TP2, le titre et chaque symptôme des 42 articles, et des débuts de phrase plus variés (« Please help: », « IT support request: »…). 805 incidents au lieu de 350. F1 macro sur son jeu de test : 0,924 (0,856 au TP5).
2. **Le second avis de la base** (`api/model.py`, `SEUIL_BASE = 0,25`) : quand la confiance du modèle est sous 0,60 mais que les mots sont connus, la catégorie de l'article le plus proche (`kb.article_le_plus_proche`) est retenue si sa similarité atteint 0,25. Les réponses de `/predict` et `/assist` disent qui a choisi (`source` : `modele`, `base` ou `aucune`), et la page l'affiche dans le tableau du fichier (« decided by »). Sur le fichier de 1 000 tickets : 588 choisis par le modèle, 69 par la base, 343 au tri.
3. **Le garde-fou de vocabulaire ignore les mots vides** (`src/predict.py`, `part_connue`) : « Our coffee machine leaks water on the floor » passait le garde-fou parce que « our », « on » et « the » comptaient comme des mots connus. Les 10 messages hors sujet vont maintenant tous au tri. Une autre langue et le charabia y vont toujours, même quand un mot (« VPN ») ressemble à un article : le second avis ne s'applique jamais sous le garde-fou.

**Ce qui reste faux.** Au jeu d'or, trois erreurs franches sont déclarées (colonne `erreur_connue`, tests en `xfail` strict) : « It does not work » (déjà déclarée au TP4), la négation « Nothing is wrong with the network, it is the keyboard… » (le second avis retient « network »), et « Teams calls drop… screen sharing freezes » (la base retient l'article des réunions, `logiciel`, là où le jeu d'or attend `reseau` : les deux se défendent). Dans le jeu d'évaluation, `securite` et `materiel` restent les plus hésitants (7 et 6 hésitations sur 12) : dans la conversation, ces incidents passent par les boutons de catégories.

**Les limites de la mesure.** Le jeu d'évaluation a été écrit par la même personne que la base, et les deux derniers symptômes viennent du fichier du binôme : les chiffres sont honnêtes mais pas indépendants. Les seuils ont été choisis sur le jeu d'évaluation **et** sur les 50 messages de développement, pour limiter le surapprentissage d'un seul jeu. Un jeu étiqueté par le membre B, jamais vu, donnerait une mesure plus sûre.

**Les tests qui fixent la qualité** : `tests/test_evaluation.py` (au moins 60 justes, au plus 5 faux, tout le hors sujet au tri, au moins 4 justes sur 12 dans chaque catégorie), et dans `tests/test_api.py` le second avis, le garde-fou face à une autre langue, le hors sujet. Le bilan des 30 conversations reste parfait : 10 tickets, tous attendus, en 2,5 tours en moyenne (2,7 avant).

**Sur le fichier du binôme** : `results_tp5.1.csv` (dossier de travail, hors dépôt) refait les 1 000 tickets avec la version finale. « I don't know » passe de 633 à 343, et 443 réponses changent. Les erreurs relevées dans le premier fichier sont corrigées (micro du casque, souris, clé USB, Ethernet, « meaning of life », « moon made of cheese ») ou envoyées au tri (ports USB, poste qui ne démarre pas), au lieu d'une catégorie fausse.

## 6. La priorité et la décision du fichier de tickets

Le binôme a fait passer `exemple_test.csv` (500 messages avec la catégorie attendue) dans la page « A file of tickets » (`results (2).csv`). Les catégories étaient celles attendues du modèle, mais deux défauts sont apparus :

- **La priorité ignorait la négation** : 27 des 31 messages « not urgent » étaient `high`, et 266 messages sur 500 étaient `high`. Au TP2, le jeu de démonstration tirait la priorité de la seule fin de phrase, sans jamais écrire « not urgent ».
- **La décision du fichier ne suivait pas la conversation** : 384 messages sur 500 en « escalade », surtout pour la priorité haute (158), alors que la conversation ne crée plus de ticket pour une priorité haute.

**Mesure honnête d'abord.** `exemple_test_2.csv` (dossier de travail, hors dépôt) reprend les incidents de `exemple_test.csv` avec des formules d'urgence et de calme absentes de l'entraînement (« nothing urgent », « it can wait until next week », « ASAP », « we are completely blocked »…) et une priorité attendue par une règle écrite d'avance : urgence explicite → `high`, calme explicite → `low`, sinon `securite` et `panne_service` → `high`, le reste → `medium`.

**La règle de la priorité dans le jeu de démonstration** (`src/make_demo.py`) : la même. Chaque incident reçoit un ton (urgent, calme, neutre, neutre) ; un incident neutre prend la priorité de sa catégorie. Le calme comprend des négations (« not urgent », « not critical at all », « no need to hurry »). Des formules d'urgence qui portaient des mots d'une catégorie (« production », « customers », « money ») ont été retirées : elles tiraient la catégorie vers `panne_service` ou `facturation`.

**La variance du jeu de démonstration.** Le jeu est tiré au hasard : le même code donne de 55 à 62 justes et de 4 à 8 faux sur le jeu d'évaluation selon la graine. Comparer deux versions sur une seule graine mesurait surtout ce bruit (63 justes avant ce travail, 57 après, pour un écart moyen d'un message sur trois graines). Huit graines ont été comparées sur les **50 messages de développement** ; la graine 2 y est la meilleure (41 justes, 3 faux) et elle est retenue. Le jeu d'évaluation n'a pas servi au choix : ses chiffres restent une mesure.

**La décision de `/assist`** (`decider_tp51` dans `api/model.py`) suit maintenant la conversation : un technicien pour une catégorie incertaine (le tri N1, comme avant), un cas critique (`securite`, `panne_service`, motif `critique`) ou l'absence d'article ; sinon `solution`. La priorité haute et les articles « always » ne suffisent plus : la conversation propose d'abord les étapes. Les règles du TP4 (`decider`) restent dans le code pour rejouer la mesure « avant » de `src/bilan_tickets.py`, et leurs tests aussi.

| Mesure | Avant | Après |
| --- | --- | --- |
| `exemple_test_2.csv` : priorité exacte (455 messages) | 43 % | **63 %** |
| `exemple_test_2.csv` : messages calmes marqués `high` | 54 / 127 | **24 / 127** |
| `exemple_test.csv` : « not urgent » marqués `high` | 27 / 31 | 0 / 31 (formule désormais apprise : chiffre non indépendant) |
| Fichier de 500 messages : « escalade » | 384 (`exemple_test.csv`), 387 (`exemple_test_2.csv`) | **266**, **293** : tri N1 et cas critiques seulement |
| Jeu d'évaluation (catégorie) | 63 / 5 / 26 (une graine favorable) | **62 / 5 / 27** ; hors sujet 9 sur 10 |
| 30 conversations | 10 tickets, tous attendus | 10 tickets, tous attendus |
| Jeu d'or | 15 justes, 3 erreurs déclarées | 15 justes, 2 erreurs déclarées : « It does not work » va maintenant au tri |
| Fichier de 1 000 tickets du binôme : INDETERMINE | 34 % | 36 % |

**Ce qui reste faux.** La priorité se trompe encore sur un tiers des messages : un modèle appris sur 805 phrases synthétiques ne connaît pas toutes les façons de dire l'urgence. « Who won the football match yesterday » est classé `facturation`, à cause du mot « match » (« licence count does not match »). Les seuils de `tests/test_evaluation.py` sont placés dans la plage mesurée sur les huit graines (au moins 58 justes, au plus 6 faux, au plus 1 hors sujet classé) : ils signalent un vrai recul sans échouer sur le bruit.

## 7. Autres jeux de données

**Aucun nouveau jeu n'a été ajouté.** Les tickets inutiles venaient de la politique (hésitation → ticket) et de la base, et les erreurs du classement de son vocabulaire trop pauvre (partie 5) : le modèle Tobi-Bueck, déjà disponible, ne faisait pas mieux sur des tickets d'une ligne. Les boutons de catégories compensent les faiblesses du modèle de démonstration sur `compte_acces` et `materiel`. Le seul jeu utilisé est Tobi-Bueck, déjà retenu au TP2, pour l'historique des tickets passés, et il n'est pas versionné. Un jeu public supplémentaire pour les catégories faibles ou les messages courts reste une piste pour améliorer le modèle réel (`train.py --reel`) : il faudra d'abord le valider avec le binôme (lien, licence, taille, correspondance avec nos 7 catégories), et ne le garder que s'il améliore le F1 macro, le rappel par catégorie et le taux de tickets sur les 30 messages.

## Mesures de contrôle

| Contrôle | Obtenu |
| --- | --- |
| `python -m pytest -q` | 266 passed, 2 xfailed (erreurs déclarées du jeu d'or), 1 failed (l'auteur unique, comme au TP1) : 150 tests de plus qu'au TP5 |
| Couverture de `api/` | 99,5 % ; seuil de la CI : 95 % |
| `python src/bilan_evaluation.py` | 62 justes sur 94 (66 %), 5 faux, 27 hésitations ; hors sujet 9 sur 10 (TP5 : 40 justes, 5 faux, 49 hésitations) |
| `python src/bilan_jeu_or.py` | juste 15, abstention 3, erreur franche déclarée 2 |
| `ruff check .` ; `mypy api` | All checks passed! ; Success: no issues found in 9 source files |
| API réelle (port 8010) et page (port 8511) | `/health` : 42 articles, `"llm": "off"` ; la page répond 200 |
| Conversation réelle « The webcam is not detected during video calls » | boutons (Hardware en premier), article « Webcam, microphone or headset not detected », « Solved » : aucun ticket, taux 100 % |
| Page réelle (AppTest sur l'API HTTP) : « I clicked a link in a suspicious email and typed my password. » | « This looks critical… shall I create a ticket? » ; après « Yes » : `Ticket TCK-AE375305 created and sent to the Security (SOC) team (status: Open).` |

Un essai à la main dans un navigateur reste à faire (voir le journal).
