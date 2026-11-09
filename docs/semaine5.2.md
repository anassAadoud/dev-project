# Semaine 5.2 : un agent qui comprend mieux les vrais messages, notes du binôme

> Étape ajoutée entre le TP5.1 et le TP6. Même architecture (page → `ui/client.py` → HTTP → API → modèle +
> base de connaissances), mêmes règles des tickets que le TP5.1. Chaque phase est mesurée avant d'être gardée.

## La méthode de mesure

**Le problème** (audit de fin de TP5.1) : les chiffres du TP5.1 étaient trop optimistes. 94 % des phrases de
test du jeu de démonstration partageaient leur symptôme avec l'entraînement (F1 0,907 sur un découpage au hasard),
et les jeux écrits à la main avaient servi à régler les seuils.

**Les jeux et leur rôle** (tous écrits avant toute modification du TP5.2) :

| Jeu | Taille | Rôle |
| --- | --- | --- |
| `data/jeu_validation.csv` | 120 (15 par catégorie, 15 hors sujet), priorité attendue | **le seul jeu de réglage** |
| `data/jeu_independant.csv` | 126 (16 par catégorie, 14 hors sujet), priorité attendue | lu deux fois : mesure de départ (phase 1) et mesure finale (phase 7) ; jamais pour décider |
| Tobi-Bueck, partie test (20 %) | 1 691 tickets réels | mesure réelle de départ et finale ; sa partie entraînement sert au mode `--mixte` |
| `data/jeu_melanges.csv` | 36 (22 messages mêlés, 14 pièges) | décider de la règle des messages mêlés (phase 3) |
| `jeu_evaluation`, `jeu_or`, `conversations_30` | 94, 20, 30 | jeux déjà vus : tests de régression, et veto (un gain de validation qui s'inverse ici n'est pas gardé) |

`tests/test_evaluer.py` vérifie qu'aucun message n'est commun à deux jeux, ni au jeu de démonstration, ni aux
symptômes de la base (trois phrases ont été reformulées avant la première mesure pour cette raison).

**Les mesures** (`python src/evaluer.py <jeu> [--graines N] [--json fichier]`) : exactitude, F1 macro et
pondéré, précision / rappel / F1 par catégorie, matrice de confusion, abstention, couverture et exactitude quand
l'agent répond, erreur de calibration (ECE), part du hors sujet refusé, priorité exacte et sa matrice, messages
calmes marqués `high`, taux d'escalade, fausses escalades (incident non critique envoyé au technicien), faux cas
critiques, cas critiques manqués. Avec `--graines`, le même code est entraîné sur des jeux de démonstration tirés
avec d'autres graines : un écart plus petit que la variation entre graines n'est pas un gain.

**Le découpage honnête** : `make_demo.py` écrit le symptôme d'origine de chaque phrase (colonne `groupe`) et
`train.py` mesure aussi le F1 d'un modèle qui n'a jamais vu les symptômes du test (`f1_macro_par_groupe`). Le F1
du cours (découpage au hasard) reste affiché et testé.

## Phase 1 : la mesure de départ (modèle du TP5.1)

| Mesure | Validation (120) | Indépendant (126) | Tobi-Bueck test (1 691) |
| --- | --- | --- | --- |
| Exactitude (catégorie) | 55,2 % | 52,7 % | 0,5 % |
| F1 macro | 0,676 (5 graines : 0,635 ± 0,021) | 0,658 | 0,017 |
| Abstention | 40,0 % | 41,1 % | 99,2 % |
| Exactitude quand l'agent répond | 92,1 % (5 faux) | 89,4 % (7 faux) | 61,5 % |
| Hors sujet refusé | 93 % | 93 % | — |
| Priorité exacte | 79,0 % | 71,4 % | 37,8 % (étiquettes réelles) |
| Escalade / fausses escalades | 60,8 % / 40,0 % | 60,3 % / 40,0 % | 99,4 % / 99,3 % |
| Faux cas critiques | 0 | 1 | 0 |

F1 du cours 0,907, F1 par symptôme **0,631**. Sur les tickets réels (longs courriels), le garde-fou de
vocabulaire écarte presque tout : le modèle de démonstration ne connaît pas ces mots.

## Phase 2 : le modèle et les données

Chaque option est comparée sur la validation, moyenne de 3 graines :

| Configuration | Exactitude | F1 macro | Faux | Abstention | Hors sujet refusé | Tobi validation (F1, textes courts) |
| --- | --- | --- | --- | --- | --- | --- |
| C0 origine (mots) | 0,511 ± 0,029 | 0,641 | 5,0 | 0,44 | 0,96 | 0,261 |
| C1 mots + caractères 2-5 | 0,559 ± 0,004 | 0,689 | 5,0 | 0,39 | 0,96 | 0,312 |
| C2 C1 + copies réécrites | 0,587 ± 0,025 | 0,708 | 6,3 | 0,35 | 0,93 | 0,319 |
| **C3 C2 + applications** | **0,635 ± 0,031** | **0,750** | **4,3** | 0,32 | 0,89 | 0,302 |
| C4 C3 + Tobi-Bueck, poids 0,05 | 0,641 | 0,736 | 8,3 | 0,28 | 0,93 | 0,639 |
| C5 C3 + Tobi-Bueck, poids 0,15 | 0,625 | 0,726 | 8,3 | 0,30 | 0,93 | 0,669 |
| C6 C3 + Tobi-Bueck, poids 0,40 | 0,616 | 0,718 | 8,3 | 0,30 | 0,93 | 0,677 |

- **Mots + caractères** (`train.CARACTERES`) : les n-grammes de caractères reconnaissent les fautes de frappe et
  les mots jamais vus. Le garde-fou de vocabulaire lit toujours les mots seuls (`predict.vectoriseur_mots`).
- **Copies réécrites** (`make_demo.AUGMENTATION`) : chaque incident a une copie écrite « vite » (minuscules,
  abréviations `pwd`, `pls`, `pc`, `asap`…, une ou deux fautes, parfois coupée). La copie garde le groupe du
  symptôme : elle reste du même côté du découpage. Une copie coupée perd sa formule d'urgence : elle prend la
  priorité de sa catégorie (sans cela, la priorité tombait de 83 % à 64 %).
- **Applications** (`make_demo.APPLICATIONS`) : Outlook, Teams, OneDrive, SharePoint, Excel, Word, PowerPoint,
  Windows, Chrome, Acrobat, Zoom, dans **plusieurs** catégories (« Teams is down for everyone » est une panne,
  « Teams will not start » un logiciel, « Teams says access denied » un compte).
- **Tickets réels mêlés** (`python src/train.py --mixte`) : le F1 sur la validation de Tobi-Bueck passe de 0,30 à
  0,67, mais les erreurs franches doublent sur les messages courts. Le mode reste une option (il demande le
  téléchargement de Tobi-Bueck) ; la CI et le modèle par défaut restent sur la démonstration.
- **Le modèle d'origine reste un repli** : `python src/train.py --origine` (mots seuls).
- **Messages trop vagues** (`predict.est_vague`) : « It does not work », « it is broken, please help » n'ont aucun
  mot qui décrive l'incident ; ils ne sont jamais tranchés (le chat pose une question). « phishing?? » l'est.

F1 par symptôme : 0,631 → 0,702 ; F1 du cours 0,907 → 0,919.

## Phase 3 : hors sujet, seuils, messages mêlés, priorité

**Hors sujet.** Le modèle apprend une classe `hors_sujet` (40 messages non informatiques, sur des sujets écartés des
jeux de mesure). L'API répond INDETERMINE avec `source: hors_sujet`, le fichier de tickets l'envoie au tri avec
le motif `hors_sujet`, le chat explique qu'il ne traite que l'informatique et laisse choisir une catégorie.

**Seuils.** Sur la validation, 3 graines, score = justes − 2 × faux :

| Essai | Résultat | Décision |
| --- | --- | --- |
| Seuil de la base 0,25 → 0,20 | validation 72,0 → 75,0, mais jeu du TP5.1 : 5 faux de plus | **non** : gain non robuste |
| Marge entre la 1re et la 2e catégorie (0,1 à 0,3) | aucun gain | non retenue |
| Calibration isotone au lieu de sigmoïde | ECE 0,085 au lieu de 0,094, score plus bas | sigmoïde gardée |
| Seuil d'abstention 0,45 à 0,70 | 0,60 reste le meilleur | inchangé |
| Classe hors sujet | validation : justes 80,0 → 82,3, faux 4,3 → 5,3, hors sujet 0,89 → 0,93 | oui |
| « Tout le monde est touché » → panne de service | validation : faux 5,3 → 4,0 ; jeu du TP5.1 : 6,0 → 4,0 | **oui** |

La règle de panne (`priorite.impact_general`) : un incident `logiciel`, `compte_acces` ou `reseau` qui touche
« the whole company », « every employee », « nobody », « all users »… est une panne de service.

**Messages mêlés** (`predict.partie_principale`). Testé sur 36 messages variés (`data/jeu_melanges.csv`, aucun du
jeu de démonstration), moyenne de 3 graines :

| Règle | Messages mêlés justes | Pièges justes |
| --- | --- | --- |
| aucune | 74 % | 98 % |
| étroite (« but the real problem is ») | 76 % | 98 % |
| **large** (vrai problème annoncé : « the issue is », « turns out », « what's really broken is » ; ou première partie réglée : « fixed », « works again », « not the Wi-Fi »… puis un connecteur) | **82 %** | 98 % |

Le gain de la règle étroite ne tenait que sur la formule du jeu de démonstration (10-27 % → 60-70 % sur ses
phrases, +2 points ailleurs) : elle a été élargie. Les pièges (« The VPN connects but I can't open the shared
drive ») ne sont pas coupés.

**Priorité à part** (`src/priorite.py`). La règle écrite : calme explicite (négations comprises) → `low` ; urgence
explicite ou impact (« ASAP », « whole team », « all customers », « in ten minutes »…) → `high` ; sinon la
catégorie (sécurité, panne → `high` ; le reste → `medium`) ; le modèle appris en repli si la catégorie est
inconnue. Sur les 105 incidents de la validation :

| Approche | Priorité exacte |
| --- | --- |
| modèle appris (TP5.1) | 76 % |
| **indices + catégorie prédite** | **86 %** |
| indices + catégorie attendue (plafond) | 95 % |
| indices seuls, sinon modèle | 83 % |
| modèle appris sur les vraies priorités Tobi-Bueck | 50 % : leurs priorités ne suivent pas cette règle, non retenu |

**Bilan de la phase 3** (validation, 3 graines) : exactitude **0,663 ± 0,020**, F1 macro **0,776 ± 0,012**, faux
**4,0** (de 3 à 5), exactitude quand l'agent répond 95,7 %, priorité exacte **0,870**, fausses escalades 33 %,
hors sujet refusé 93 %. Les 30 conversations du TP5.1 donnent toujours 10 tickets, tous attendus.

## Phase 3 bis : la qualité des réponses

**Le problème.** Au TP5.1, l'agent cherchait l'article **dans la catégorie prédite seulement** : une erreur du
classifieur, ou une abstention (30 % des incidents de la validation), privait l'utilisateur du bon article.

**Ce qui a changé.**

- **Recherche dans toute la base** (`kb.proposer`) : les 3 meilleurs articles, toutes catégories confondues ; la
  catégorie prédite donne un bonus (`BONUS_CATEGORIE = 0,10`) ; index de recherche mots + caractères 3-5 (fautes de
  frappe). Les mots du temps (« yesterday », « monday », « hours »…) ne décrivent pas l'incident : ils rejoignent les
  mots génériques de la règle des messages vagues. Le second avis de classement (`article_le_plus_proche`) garde l'index de mots, sur lequel `SEUIL_BASE`
  est réglé. Un message trop vague n'a pas d'article.
- **Quand le modèle hésite**, l'agent montre les 3 articles les plus proches à côté des boutons de catégories
  (« Does one of these articles match your problem? ») ; choisir un article donne sa catégorie à la conversation.
  Le hors sujet et les mots inconnus n'ont pas d'article.
- **Suggestions** : à côté de l'article retenu, les deux suivants, que l'utilisateur peut choisir (`choisir_article`).
- **Base de connaissances** : 42 → **57 articles** (8 par catégorie, 9 en logiciel), chaque article avec des étapes
  vérifiables (menu, raccourci, commande, chemin ou adresse : `Settings > Network & internet > Wi-Fi > Manage known
  networks`, `ipconfig /flushdns`, `outlook.exe /safe`, `https://mysignins.microsoft.com`…), un champ `escalade_si`,
  et une colonne `source` pour les 26 articles dont une étape vient d'une documentation officielle (Microsoft
  Support, Microsoft Learn). `tests/test_reponses.py` vérifie ces règles article par article.
- **Questions de diagnostic** (`data/questions_diagnostic.json`, 2 ou 3 par catégorie) : « Is it only you, or
  everyone around you? », « How are you connected? », « Which application is it? »… La question s'affiche à côté de
  l'article ; la réponse fait passer des articles devant, ou change la catégorie : « Everyone in the office » fait
  du réseau ou du logiciel une **panne**, et l'agent propose le ticket critique, **toujours confirmé**. Les
  réponses citent des articles qui existent : l'API refuse de démarrer sinon (`charger_questions`).
- **Les règles des tickets du TP5.1 ne changent pas** : ni le choix d'un article ni une réponse de diagnostic ne
  comptent comme une tentative ; jamais de ticket au premier message ; un seul ticket par conversation.
- `/assist` renvoie aussi `articles` (les 3 meilleurs) ; `/chat` renvoie `suggestions` et `question`.

**La mesure** (`python src/evaluer_articles.py validation --methode …`). Les 105 incidents de la validation portent
maintenant les articles qui les règlent (colonne `articles_ok`, écrite d'après le texte des articles, sans regarder
les réponses de l'agent). top-1 : le premier article proposé est un bon article ; top-3 : un des trois l'est. Un
incident sans article compte comme manqué.

| Configuration | top-1 | top-3 | Sans article |
| --- | --- | --- | --- |
| **Avant** (commit de la phase 3 : base de 42 articles, modèle entraîné dessus, catégorie prédite seulement) | **52,4 %** | **58,1 %** | 36,2 % |
| Base de 57 articles, catégorie prédite seulement | 59,0 % | 64,8 % | 31,4 % |
| + toute la base (bonus de catégorie), rien quand le modèle hésite | 61,9 % | 68,6 % | 29,5 % |
| **+ articles aussi quand le modèle hésite (retenu)** | **75,2 %** | **85,7 %** | 1,0 % |
| + une réponse au diagnostic (utilisateur simulé qui choisit la réponse qui cite un bon article) | 79,0 % | 86,7 % | 1,0 % |

- Le gros du gain vient des abstentions : le modèle hésite sur 30 % des incidents, mais la base connaît souvent
  l'article.
- Le premier essai du diagnostic **faisait baisser** le top-1 (67,6 %) : les articles d'une réponse passaient
  devant dans l'ordre du fichier. Ils ont maintenant le même bonus et la similarité les départage (79,0 %).
- **Effet sur le classement** : le jeu de démonstration lit les symptômes de la base, donc le modèle change aussi.
  Validation, 3 graines : exactitude 0,654 → **0,686**, F1 macro 0,768 → **0,791**, faux 4,0 → 4,3 (de 3 à 6),
  fausses escalades 34,7 % → 27,1 %. Veto (jeux déjà vus) : jeu du TP5.1 F1 0,793 → 0,807, faux 4,0 → 4,0 ; jeu
  d'or 0,844 → 0,857. Le F1 par symptôme du jeu de démonstration baisse (0,727 → 0,683) : de nouveaux symptômes,
  plus proches entre catégories ; la validation, qui seule décide, monte.
- Les 30 conversations du TP5.1 donnent toujours **10 tickets, tous attendus**, 0 écart.
- Une phrase de la validation a été reformulée avant la mesure (« scanner jams on every page ») : elle était devenue
  un symptôme de la nouvelle base (contrôle des fuites de `tests/test_evaluer.py`).
- Le jeu indépendant a reçu ses `articles_ok` dans le même commit, d'après le texte des articles, **sans faire
  tourner l'agent dessus** : il sera mesuré une seule fois, en phase 7.

## Phase 4 : l'hybride TF-IDF + MiniLM

**L'essai.** Le notebook `minilm_vs_tfidf.ipynb` (tickets Tobi-Bueck) avait montré que MiniLM seul perdait 5 points
de F1 et que l'hybride en gagnait 2 : seul l'hybride est essayé. `python src/essai_minilm.py` entraîne le même code
sur 3 graines du jeu de démonstration et compare, sur la validation :

- **actuel** : mots + caractères → LinearSVC calibré (modèle de la phase 3 bis) ;
- **H1** : mots + caractères + vecteurs all-MiniLM-L6-v2 (dimension 384, normalisés) côte à côte → même classifieur ;
- **H2** : H1, et la recherche d'articles lit aussi les vecteurs MiniLM.

| Validation, 3 graines | F1 macro | Exactitude | Faux | top-1 | top-3 | Escalade (tickets du fichier) | Fausses escalades | ms / message |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| actuel | 0,791 ± 0,002 | 0,686 | 4,3 | 74,9 % | 85,7 % | 52,2 % | 27,1 % | 4 à 11 |
| H1 | **0,847 ± 0,002** | 0,759 | 3,0 | 78,4 % | 87,0 % | 50,8 % | 22,7 % | 24 à 45 |
| **H2 (retenu)** | **0,847 ± 0,002** | **0,759** | **3,0** | **81,9 %** | **96,2 %** | 50,8 % | 22,7 % | 83 à 100 |
| H2, poids MiniLM 0,5 | 0,828 | 0,737 | 4,0 | 81,0 % | 95,2 % | 51,1 % | 24,4 % | — |
| H2, poids MiniLM 2,0 | 0,850 | 0,765 | 3,0 | 82,5 % | 96,2 % | 50,6 % | 22,2 % | — |

- **Règle de décision** (fixée avant l'essai) : l'hybride n'est gardé que s'il gagne au moins 5 points de F1 macro
  ou de top-3. H2 gagne **+5,6 points de F1** et **+10,5 points de top-3** : il est gardé.
- **Poids** : 2,0 fait +0,3 point de F1, moins que l'écart entre graines ; 1,0 est gardé (plus simple).
- **Veto** (jeux déjà vus) : jeu du TP5.1, F1 0,807 → 0,853, faux 4,0 → 3,3, fausses escalades 24,4 % → 18,9 % ;
  jeu d'or, identique (0,857). Aucun recul.
- **Le temps** : environ 0,1 s par message sur le processeur du poste (encodage MiniLM d'une phrase, une fois :
  le classement et la recherche partagent le vecteur, `encodeur.Phrases`). Le chargement de l'encodeur se fait au
  démarrage de l'API (quelques secondes), pas à la première requête.
- **Le modèle enregistré** (`python src/train.py`) : validation, exactitude 75,2 %, F1 macro 0,846, 2 faux, hors
  sujet refusé **100 %** (93 % avant), top-1 81,9 %, top-3 96,2 % (86,7 % de top-1 après une réponse au diagnostic) ;
  F1 par symptôme du jeu de démonstration 0,683 → 0,736. Les 30 conversations du TP5.1 : 10 tickets, 0 écart.

**L'intégration.**

- `src/encodeur.py` : `Phrases`, l'étape « phrases » du `FeatureUnion` de `train.construire_pipeline` et de l'index
  de `kb.py`. Le **mode** (`minilm` ou `factice`) est choisi à l'entraînement (`SUPPORT_ENCODEUR`) et gardé dans le
  modèle ; la recherche d'articles suit le modèle servi. Un cache borné (5 000 textes) évite de réencoder.
- **Encodeur factice** dans la CI (`SUPPORT_ENCODEUR=factice`) : des n-grammes hachés de même dimension, sans
  téléchargement ni sentence-transformers. La CI simulée sur une copie du dépôt : tous les tests passent, couverture
  de l'API 98,9 %.
- **Un test lent** (`@pytest.mark.lent`, `tests/test_encodeur.py`) utilise le vrai MiniLM : deux formulations du même
  incident sans mot commun sont plus proches qu'un autre incident. Ignoré si le modèle n'est pas dans le cache ; la
  CI lance `pytest -m "not lent"`.
- **Sans MiniLM**, l'API refuse de démarrer avec un message qui dit quoi faire ; le repli reste
  `python src/train.py --sans-minilm` (le modèle de la phase 3 bis).
- **Règle des messages mêlés** : la CI (encodeur factice) a montré que deux pièges étaient coupés (« The issue is
  that my account is disabled… » : la règle retirait l'annonce, il n'y a pourtant pas de première partie). Un message
  qui commence par l'annonce n'est plus coupé : messages mêlés 20 / 22 justes avant et après, pièges coupés 2 → 0.

## Phase 5 : l'interface et les escalades

**L'onglet « A file of tickets »** (`ui/fichier.py`, testé sans Streamlit par `tests/test_fichier.py`) :

- **Lecture tolérante** : UTF-8 avec ou sans BOM, Windows-1252, Latin-1 ; séparateur virgule, point-virgule ou
  tabulation, lu sur l'en-tête (les textes contiennent des virgules) ; colonne `text` sans tenir compte de la casse ;
  un fichier d'une seule colonne garde chaque ligne entière ; lignes vides ignorées ; 5 Mo et 2 000 tickets au plus
  (au-delà, un avertissement : seuls les 2 000 premiers sont traités). Les trois fichiers du dossier de travail se
  lisent (`exemple_test.csv`, `exemple_test_2.csv` : 500 tickets ; l'export du 9 novembre : 1 000, ses anciennes
  colonnes de résultat sont remplacées).
- **Résultats** : catégorie, confiance, priorité, décision et sa raison en clair, équipe, qui a décidé, **l'article
  proposé et ses étapes**, et une colonne `critical`. Une barre de progression pendant le tri ; le fichier n'est trié
  qu'une fois (Streamlit relance le script à chaque clic). Téléchargement en UTF-8 avec BOM : Excel l'ouvre avec les
  accents.
- **Cas critiques** (sécurité, panne générale) : comptés à part ; la page propose leurs tickets **tout de suite**,
  et ne les crée qu'après une case « Yes, create N ticket(s) » cochée puis le bouton (`client.creer_tickets_critiques`).
  Aucun ticket n'est créé par le seul tri du fichier (vérifié par un test).

**La conversation** (rappel des règles du TP5.1, inchangées et testées) : jamais de ticket au premier message ; un
cas critique propose le ticket dès le premier message, avec les étapes de l'article, et attend la confirmation ; un
seul ticket par conversation, pré-rempli (résumé, catégorie, étapes déjà essayées). Nouveau en phase 3 bis : un
article critique choisi parmi les suggestions, ou la réponse « Everyone in the office » au diagnostic, propose aussi
le ticket critique, toujours confirmé.

**Ce que l'analyse de l'export du 9 novembre avait montré** (1 000 tickets triés par le modèle du TP5.1) : 211
incidents informatiques envoyés au tri, dont des cas de sécurité (« An employee clicked a phishing link and entered
their credentials ») ; « ransomware note on my screen » encore indéterminé (confiance 0,60, juste sous le seuil).
Le modèle de la phase 4 réduit l'abstention (22,9 % de la validation au lieu de 29,5 %) ; dans le fichier, les
incidents indéterminés partent toujours au tri N1, jamais perdus.

## Phase 6 : sécurité et fiabilité de l'API

Tout est dans `api/securite.py` et testé par `tests/test_securite.py` (22 tests) :

| Risque | Avant | Après |
| --- | --- | --- |
| Requête énorme (mémoire, temps) | aucune limite de corps | **128 Ko** au plus, annoncés ou envoyés par morceaux → 413 ; le plus gros `/chat` légitime fait 72 Ko |
| Champs sans limite | `etapes_faites` (chaque étape), `raison`, identifiants, `tour` | 500 caractères par étape, 500 pour la raison, 40 pour un identifiant, tour ≤ 1 000 |
| Identifiants arbitraires (`../..`, 500 caractères) | lus dans le stockage | formats `CNV-XXXXXXXX` et `TCK-XXXXXXXX` vérifiés : sinon 404, **sans lire le stockage** |
| Un refus renvoie le texte reçu | le 422 de FastAPI contient `input` (le texte de l'employé) | `loc`, `msg`, `type` seulement : la forme standard que les tests du TP4 vérifient |
| Panne imprévue hors des routes protégées | réponse de Starlette | gestionnaire global : journalisée côté serveur, le client reçoit « Erreur interne du serveur », ni trace ni chemin |
| CORS | tous les sites, avec cookies | `SUPPORT_ORIGINES` (par défaut la page Streamlit locale), sans cookies, GET / POST / PATCH |
| Mise en cache, cadres | rien | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` |
| Ligne abîmée dans `tickets.jsonl` (écriture coupée) | plus aucun ticket lisible (500) | ligne ignorée et journalisée, les autres restent lisibles |

**Modèle, base, questions ou encodeur absents** : l'API **refuse de démarrer** avec un message qui dit quoi faire
(règle du TP4 : mieux vaut ne pas démarrer que répondre faux), y compris pour `data/questions_diagnostic.json`
(nouveau test) et pour MiniLM (phase 4). Un modèle retiré pendant que l'API tourne répond 503.

**Non traité** (noté pour le TP6) : pas d'authentification (l'API est faite pour un réseau interne, derrière la
page), pas de limite de débit par client, et les tickets restent en fichiers JSON Lines sans chiffrement.
