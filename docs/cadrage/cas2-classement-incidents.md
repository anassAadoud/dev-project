# Fiche de cadrage : Classement des incidents informatiques

> Remplir chaque rubrique en une à trois phrases. Les rubriques marquées (obligatoire) sont vérifiées par `pytest`.

## Besoin en une phrase (obligatoire)

Classer un incident décrit en texte libre, en anglais, dans l'une des sept catégories IT (sécurité, réseau, matériel, comptes et accès, facturation, logiciel, panne de service), avec une confiance qui permet de s'abstenir.

## Utilisateur final (obligatoire)

L'utilisateur qui signale un incident voit la catégorie retenue ; derrière lui, l'agent s'en sert pour chercher une solution et choisir le groupe d'escalade, et le technicien la reçoit dans le ticket.

## Approche retenue (obligatoire)

Cocher une seule case :

- [ ] Règles métier
- [x] Machine learning
- [ ] RAG
- [ ] Modèle génératif seul

## Justification (obligatoire, citer au moins deux critères de la grille : (a) données étiquetées, (b) vérifiabilité, (c) coût par requête, (d) conséquence d'une erreur)

(a) Le jeu public Tobi-Bueck contient 9 179 incidents en anglais après nettoyage, dont 8 266 reçoivent une catégorie IT tirée de leurs tags : des données étiquetées existent, même si ces étiquettes sont construites par nous. (c) Un modèle TF-IDF linéaire répond en quelques millisecondes, sans GPU ni appel payant, pour des centaines d'incidents par jour. (d) Une erreur de catégorie envoie l'incident vers le mauvais groupe : on la limite par l'abstention (`INDETERMINE` vers le tri N1) quand la confiance est basse ou que les mots sont inconnus. (b) Les performances se mesurent sur un jeu de test tenu à l'écart.

## Données nécessaires et leur origine (obligatoire)

`Tobi-Bueck/customer-support-tickets` (Hugging Face, CC BY-NC 4.0) : tickets fictifs, filtrés sur `language == "en"` et `type == "Incident"`, texte = sujet + corps, doublons retirés ; la catégorie vient de la première règle de tags qui correspond (section 15.2 du notebook). Pour la CI et les tests, un jeu synthétique anglais généré par `src/make_demo.py`, sans réseau.

## Métrique de succès et seuil d'acceptation (obligatoire)

F1 macro sur le jeu de test (20 %, découpé avant la vectorisation). Référence mesurée dans le notebook : 0,788 sur Tobi-Bueck avec LinearSVC calibré, contre 0,072 pour la référence naïve ; le seuil du cours (0,85) n'est pas atteint sur les données réelles, ce qui est documenté plutôt que masqué. Acceptation : F1 macro au moins 0,85 sur le jeu de démonstration, au moins 0,75 sur Tobi-Bueck, et les deux pièges (texte en français, charabia) en `INDETERMINE`.

## Conséquence d'une erreur et validation humaine prévue (obligatoire)

Une catégorie fausse propose une solution inadaptée ou envoie le ticket au mauvais groupe, ce qui retarde la résolution. L'utilisateur indique si la solution a marché ; sinon le ticket part vers un humain, et le technicien peut corriger la catégorie, ce qui fournit de nouveaux exemples.

## Risques éthiques ou de confidentialité (obligatoire)

Le jeu Tobi-Bueck est fictif et public, mais sa licence interdit l'usage commercial. Les incidents réels saisis dans l'application peuvent contenir des données personnelles : pas de stockage dans Git, pas d'envoi à un service tiers. Le modèle ne comprend que l'anglais : un utilisateur qui écrit dans une autre langue doit être orienté vers un humain, pas mal classé.

## Approche écartée et pourquoi (facultatif)

Les règles par mots-clés manquent les formulations variées (« can't log in », « locked out », « access denied »). Un modèle génératif seul coûterait à chaque appel, serait difficile à mesurer et à reproduire, et il est exclu des TP1 à TP6.
