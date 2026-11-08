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
