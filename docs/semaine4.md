# Semaine 4 : tests approfondis et qualité, notes du binôme

> Uniquement des chiffres issus de nos exécutions, modèle de démonstration (celui de la CI) sauf mention contraire.

## 1. Couverture

- **Avant** (étape A, `pytest --cov=api --cov-report=term-missing`) : **94 %**. `api/main.py` 91 % (lignes 54, 89-90, 104-105, 125-127), `api/model.py` 94 % (57, 59), `api/tickets.py` 96 % (36), `api/schemas.py` 100 %.
- Ce qu'aucun test ne vérifiait :
  - `main.py` ligne 54 : la réponse **503** quand le modèle n'est pas chargé ;
  - lignes 89-90 et 104-105 : la conversion d'une `ValueError` en **422** dans `/assist` et `/tickets`. Personne n'avait vu qu'une panne interne y passait pour une faute du client (défaut 4) ;
  - lignes 125-127 : le lancement direct `python api/main.py`, qui n'est pas une réponse de l'API ;
  - `model.py` lignes 57 et 59 : deux règles d'escalade de la fiche `cas1`, « aucun article » et « article qui demande toujours un technicien » ;
  - `tickets.py` ligne 36 : la lecture d'un ticket avant que le fichier existe.
- **Après** (étape D, puis E) : **99,07 %** (seuil de la CI : 95 %). Seules les lignes du bloc `if __name__ == "__main__":` de `main.py` restent non exécutées. Nous ne les avons pas exclues : elles ne font que lancer uvicorn, ce que l'on vérifie à la main, et un `# pragma: no cover` n'apporterait qu'un chiffre plus flatteur. Aucune exclusion dans le dépôt.

## 2. Défauts trouvés

| Symptôme | Test qui l'a révélé | Correction |
| --- | --- | --- |
| `{"text": "   "}` reçoit 422, mais `detail` est une chaîne (`"texte vide"`) au lieu de la liste standard : deux formes pour un même refus | `test_frontieres_du_contrat[texte-espaces]` | `field_validator` (`pas_que_des_blancs`) dans `PredictRequest` et `TicketRequest` |
| Hypothesis trouve le contre-exemple minimal `texte='\x85'` : accepté par le schéma (1 caractère), refusé par `predict()`, car `str.strip()` le retire | `test_tout_texte_de_blancs_est_refuse` | Même validateur, avec la règle exacte de `predict()` : `not valeur.strip()` |
| Les mots inventés reçoivent un verdict forcé (`logiciel`, 0,1766 : vecteur TF-IDF nul, seule la classe a priori répond) ; surtout, « Mon VPN ne se connecte plus depuis ce matin » reçoit `reseau` à **0,8151** sur un seul mot connu | Essais dans l'API, puis `courbe_seuil.py` | `SEUIL_ABSTENTION = 0.60` **et** garde-fou de vocabulaire (`SEUIL_VOCABULAIRE = 0.50`, part de mots connus renvoyée par `predict()`) : les deux deviennent `INDETERMINE`, l'incident va au tri N1 |
| Une panne interne `ValueError("bug interne")` répond **422** sur `/predict`, `/assist` et `/tickets`, avec le message interne renvoyé au client ; une `RuntimeError` n'est pas rattrapée du tout | `test_panne_du_modele_repond_500` (6 cas, tous en échec avant correction) | Toute exception du modèle répond 500, message générique, `raise ... from None`, panne journalisée côté serveur |
| Un modèle ou une base placés **hors du dépôt** font lever `ValueError` au lieu de `FileNotFoundError` : le message d'erreur appelait `relative_to(RACINE)` | `test_refus_de_demarrer_sans_modele`, `test_refus_de_demarrer_sans_base` (le chemin de test est dans un dossier temporaire) | Message avec le chemin complet. Ce défaut aurait cassé la variable `SUPPORT_MODELE` du TP6 |
| Les étiquettes du modèle passaient au contrat sans contrôle ; mypy ne voyait rien (`dict`, donc `Any`) | mypy, une fois `Prediction` typé : `Incompatible types in assignment (expression has type "str", variable has type "Literal[...]")` pour la catégorie et la priorité ; puis `test_refus_des_etiquettes_inconnues` | `TypedDict` (`Prediction`, `Assistance`, `Resultat`), `Literal` du contrat, correspondances explicites `CORRESPONDANCE` et `PRIORITES` vérifiées au démarrage |

Résultat final : `python -m pytest -q` donne **103 passed, 1 xfailed, 1 failed**. Le seul échec est `test_each_member_has_committed` (le membre B n'a pas encore commité, voir le journal). `tests/test_limites.py` donne 10 passed trois fois de suite.

## 3. Seuil d'abstention

Trois points de la courbe (`python src/courbe_seuil.py`), sur les deux jeux :

| seuil | démonstration (70 incidents) : répond à / exactitude / erreurs / vers le tri | Tobi-Bueck (1 691 incidents) : répond à / exactitude / erreurs / vers le tri |
| --- | --- | --- |
| 0,50 | 68 (97 %) / 0,868 / 9 / 2 | 1 563 (92 %) / 0,872 / 200 / 128 |
| **0,60** | 62 (89 %) / 0,919 / 5 / 8 | 1 405 (83 %) / 0,905 / 134 / 286 |
| 0,70 | 56 (80 %) / 0,982 / 1 / 14 | 1 247 (74 %) / 0,925 / 94 / 444 |

- **Seuil retenu : 0,60** (0,5 dans le cadrage du TP1 : changement signalé dans la fiche du projet). Part envoyée au tri N1 : **8 sur 70 (11 %)** sur la démonstration, **286 sur 1 691 (17 %)** sur les données réelles.
- Justification : de 0,50 à 0,60, les erreurs tombent d'un tiers sur les données réelles (200 → 134), pour 9 points de plus envoyés au tri. À 0,70, 26 % des incidents iraient au tri, et l'agent de premier niveau perdrait l'essentiel de son intérêt. Une erreur de catégorie a pourtant une issue : l'article proposé ne marche pas, l'utilisateur répond « non résolu » et un ticket part quand même. Sur les 12 incidents du notebook (modèle réel, TP2), 0,60 envoie au tri le VPN (0,46), l'imprimante (0,41), la base de données (0,40, de toute façon escaladée pour sa priorité haute), le laptop (0,25) et le partage refusé (0,59). Ce dernier était une erreur franche (`securite` au lieu de `compte_acces`) : le seuil l'évite.
- **Le garde-fou de vocabulaire** ne touche aucun incident du jeu de test de démonstration et un seul sur 1 691 du jeu réel. Il est fait pour les textes que le seuil ne voit pas : le message en français (11 % de mots connus, 0,8151 de confiance).

## 4. Jeu d'or

- Bilan (`python src/bilan_jeu_or.py`, 20 incidents dont 10 difficiles) : **14 justes, 5 abstentions, 1 erreur franche déclarée**.
- Ce que ces chiffres disent du modèle :
  - Les 10 incidents simples (dont 7 repris des 12 incidents du notebook) sont tous justes, avec une confiance de 0,75 à 0,93. Le modèle de démonstration connaît bien les formulations courtes de ses propres catégories.
  - Les deux incidents au vocabulaire partagé (« permission denied » sur un partage, « 500 error » d'un site) sont justes : `compte_acces` à 0,91 et `panne_service` à 0,78.
  - Sur les deux incidents mêlés, l'un est juste (« The printer was fixed yesterday, but the real problem is that I cannot log in », `compte_acces` 0,83). L'autre est en abstention (« Excel crashed… then the antivirus found a virus », 0,50) : quand deux symptômes pèsent autant, la confiance baisse et l'incident va au tri, ce qui est le comportement voulu.
  - La négation (« Nothing is wrong with the network, it is the keyboard… », 0,56), l'autre langue (11 % de mots connus), le hors-domaine (« coffee machine », 0,55) et le texte réel du notebook (« Teams calls drop… », 0,41) sont tous en abstention : aucun n'est classé franchement.
  - **L'erreur franche** : « It does not work » est classé `compte_acces` à 0,85, avec 100 % de mots connus. Ni le seuil ni le garde-fou ne la voient : un texte vague fait de mots courants obtient une confiance élevée. Nous la gardons, déclarée dans `erreur_connue`. Piste, à mesurer avant de la retenir : exiger un nombre minimal de mots connus non vides (3 par exemple) avant de répondre. Ce n'est pas fait ici, pour ne pas régler une règle sur le jeu qui sert à la juger.

## 5. Outils statiques

- Remarques au départ : ruff **1** (I001, ordre des imports dans `api/main.py`), mypy **0** (`Success: no issues found in 5 source files`). Le code avait été écrit en suivant les corrections du cours (`zip(..., strict=True)`, `raise ... from`), d'où moins de remarques que les 11 du dépôt de référence.
- Parmi les 6 défauts de la partie 2, ruff n'en a signalé **aucun**. mypy en a trouvé **un**, mais seulement après que nous avons typé `Prediction` : tant que le retour était un `dict`, il restait muet.
- Conclusion : les outils statiques vérifient la forme du code et la cohérence des types qu'on leur déclare ; ils ne savent pas ce que l'API promet. Les défauts de comportement (forme d'un refus, verdict forcé, panne déguisée en 422, chemin hors du dépôt) n'ont été trouvés que par des tests écrits depuis le contrat. Le crochet pre-commit (vérifié : un `import os` inutile fait échouer la ligne ruff et le commit n'est pas créé) et la CI empêchent les régressions de forme ; les tests empêchent les régressions de comportement.
