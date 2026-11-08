# Semaine 2 : le modèle de classement des incidents

## Mesures

| Mesure | Jeu de démonstration | Tobi-Bueck (`--reel`) |
| --- | --- | --- |
| Incidents (entraînement / test) | 350 (280 / 70) | 8 452 (6 761 / 1 691) |
| Vocabulaire | 661 termes | 28 420 termes |
| F1 macro, 7 catégories | **0,856** (seuil du cours 0,85 : atteint) | **0,789** (seuil du cours 0,85 : non atteint ; acceptation de la fiche cas2 : 0,75) |
| Exactitude | 0,857 | 0,844 |
| Erreurs sur le jeu de test | 10 sur 70 | 263 sur 1 691 |
| Priorité : F1 macro, rappel de `high` | 1,000 ; 1,000 (étiquettes déterministes du générateur) | 0,661 ; 0,717 |

Modèle : TF-IDF (1-2 grammes, `min_df=2`, `sublinear_tf`) + `LinearSVC` calibré (`CalibratedClassifierCV`, `cv=3`), `class_weight="balanced"`, graine 42, découpage 80/20 stratifié **avant** la vectorisation. Les deux modèles (catégorie, priorité) sont sauvegardés ensemble dans `models/support.joblib`, hors de Git ; `models/metrics.json` est versionné.

## Analyse des erreurs du jeu de démonstration

Sur les 70 incidents de test, le modèle commet 10 erreurs, et toutes tombent sur des incidents mêlés (15 dans le jeu de test). Exemple : « Outlook stopped receiving emails, and now, I cannot reach the intranet, DNS lookup fails » est classé `logiciel` au lieu de `reseau`. Ces incidents citent d'abord le symptôme d'une autre catégorie, puis, après un retournement (« but the real problem is that », « and now »), le vrai problème. Un sac de mots additionne les poids des deux symptômes sans savoir lequel vient en dernier. Il faudrait une représentation qui tienne compte de l'ordre et du contexte, comme les embeddings de phrase de la semaine 9. En production, un message qui décrit deux symptômes devrait plutôt baisser la confiance et finir en `INDETERMINE` (TP4).

## Ce que le notebook `tobi_bueck_incidents_v3.ipynb` a appris (copié dans `notebooks/`)

**Les 8 queues : F1 macro 0,592.** Le premier essai prédisait la colonne `queue` (8 services : Technical Support, Product Support, IT Support…) avec une régression logistique : F1 macro 0,592, exactitude 0,558, contre 0,070 pour la référence naïve. LinearSVC monte à 0,693. Les confusions les plus fréquentes sont entre *Technical Support*, *IT Support* et *Product Support* (114, 106 et 85 erreurs). Ces queues sont des services d'une entreprise fictive qui se recouvrent, pas des catégories d'incident : regroupées en 5 familles, le F1 macro passe à 0,728. Ce sont les étiquettes qui limitaient le score, pas seulement le modèle.

**Les textes courts.** Les tickets du jeu sont des courriels formels de 58 mots en médiane. Les messages d'un utilisateur dans la page en font une dizaine. Mesuré sur le sujet seul (5 mots en médiane), le F1 macro tombe de 0,592 à 0,381. Avec la régression logistique de départ, les 12 incidents de test avaient tous une confiance entre 0,17 et 0,36, donc tous en `INDETERMINE` au seuil 0,5. C'est l'écart le plus important entre l'entraînement et l'usage réel.

**Pourquoi des catégories tirées des tags.** Les colonnes `tag_*` contiennent de vraies catégories d'incident (Security, Network, Hardware, Software, Account…). Une catégorie IT est donnée par la première règle de tags qui correspond (sécurité, réseau, matériel, comptes et accès, facturation, logiciel, panne de service). **Ces étiquettes sont construites par nous**, pas par les auteurs du jeu : un ticket tagué à la fois « Security » et « Network » est classé `securite` parce que cette règle vient en premier. Le F1 macro mesure donc l'accord avec nos règles, pas avec un technicien. Avec ces catégories, le F1 macro atteint 0,788 dans le notebook et **0,789 chez nous**, contre 0,072 pour la référence naïve. Les catégories les plus faibles sont `panne_service` (0,684), `materiel` (0,691) et `compte_acces` (0,702), les moins représentées après `facturation`. Leurs incidents sont souvent absorbés par `logiciel`, qui représente 34 % du jeu.

**Le garde-fou de vocabulaire.** Un texte sans aucun mot connu donne un vecteur TF-IDF nul. Le modèle répond alors sa classe la plus probable a priori, avec une confiance qui ne dit rien : notre modèle réel donne « logiciel, 0,51 » à `xqzvb wlkptr grombu`, au-dessus du seuil de départ de 0,5. Le seuil seul ne peut donc pas attraper le charabia. Le garde-fou compte la part des mots du message que le modèle connaît, et répond `INDETERMINE` sous 50 %. Il attrape le charabia (0 % de mots connus) et le message en français (11 %), sans bloquer les 10 vrais incidents (73 % à 100 %). Il sera branché dans l'API au TP4, avec le seuil.

**Les 12 incidents de test** (modèle réel, notre `predict()`, avant abstention) :

| Incident | Catégorie | Confiance | Priorité | Mots connus |
| --- | --- | --- | --- | --- |
| My VPN keeps disconnecting every 10 minutes… | logiciel | 0,46 | medium | 0,82 |
| I can't log in, my account is locked… | compte_acces | 0,81 | medium | 0,83 |
| Outlook stopped receiving emails… | logiciel | 0,61 | low | 1,00 |
| The printer on the second floor shows offline… | logiciel | 0,41 | medium | 0,73 |
| Our production database server is down… urgent! | panne_service | 0,40 | high | 0,85 |
| My laptop is extremely slow and the fan is very loud | materiel | 0,25 | medium | 0,82 |
| The website returns a 500 error… | logiciel | 0,75 | medium | 0,91 |
| I was charged twice for my subscription… | facturation | 0,63 | low | 1,00 |
| The new software update crashes the application… | logiciel | 0,90 | high | 0,89 |
| I cannot access the shared drive anymore, permission denied | securite | 0,59 | medium | 0,88 |
| Mon VPN ne se connecte plus depuis ce matin | reseau | 0,55 | medium | 0,11 |
| xqzvb wlkptr grombu | logiciel | 0,51 | high | 0,00 |

La catégorie est celle qu'un technicien aurait choisie pour 7 des 10 vrais incidents (compte, Outlook, base de données, site web, facturation, mise à jour, laptop). Le VPN et l'imprimante partent en `logiciel` avec une confiance basse (0,46 et 0,41) : sous le seuil de 0,5, ils seraient escaladés au tri N1, ce qui est le bon comportement. La base de données en panne (0,40, priorité `high`) serait escaladée deux fois : confiance basse et priorité haute. Le partage refusé est classé `securite` au lieu de `compte_acces`, avec 0,59 : c'est une erreur franche, que seul un seuil plus haut éviterait. La courbe du seuil du TP4 dira à quel prix.

**La priorité.** F1 macro 0,661, rappel de `high` 0,717 : près de 3 incidents urgents sur 10 ne sont pas reconnus comme tels. La priorité prédite ne peut donc pas décider seule qu'un incident n'est pas urgent. La règle d'escalade (fiche `cas1`) l'utilise dans un seul sens : `high` force l'escalade, mais `low` n'empêche rien.

## Conclusion

Le seuil du cours (0,85) est atteint sur le jeu de démonstration, pas sur Tobi-Bueck (0,789). Le seuil d'acceptation de la fiche `cas2`, fixé au TP1 à 0,75 à partir du notebook, est atteint. `tests/test_model.py` applique le seuil de la source lue dans `metrics.json` : 0,85 pour la démonstration, 0,75 pour Tobi-Bueck. Comme Allociné dans le cours, Tobi-Bueck sert de mesure sur données réelles. Le modèle utilisé par la CI et les tests de l'API reste celui du jeu de démonstration, rapide et sans réseau.
