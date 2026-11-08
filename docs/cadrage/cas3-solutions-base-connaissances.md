# Fiche de cadrage : Proposer une solution tirée de la base de connaissances

> Remplir chaque rubrique en une à trois phrases. Les rubriques marquées (obligatoire) sont vérifiées par `pytest`.

## Besoin en une phrase (obligatoire)

Pour un incident classé, proposer à l'utilisateur la procédure pas à pas la plus pertinente de la base de connaissances interne, avec la référence de l'article, puis lui demander si le problème est résolu.

## Utilisateur final (obligatoire)

L'employé qui signale l'incident suit les étapes proposées ; les techniciens rédigent et valident les articles de la base, et voient dans le ticket l'article déjà essayé.

## Approche retenue (obligatoire)

Cocher une seule case :

- [ ] Règles métier
- [ ] Machine learning
- [x] RAG
- [ ] Modèle génératif seul

## Justification (obligatoire, citer au moins deux critères de la grille : (a) données étiquetées, (b) vérifiabilité, (c) coût par requête, (d) conséquence d'une erreur)

(b) La solution doit venir d'un article validé par un technicien, et l'article doit être cité (identifiant, titre) pour que l'utilisateur et le technicien sachent d'où vient la procédure. (a) Nous n'avons pas de paires question-réponse étiquetées, mais nous avons des documents : la base de connaissances et les réponses de tickets passés. (d) Une procédure inventée pourrait faire perdre des données ou ouvrir une faille : on ne montre que des étapes écrites et relues. Dans les TP1 à TP6, seule la partie recherche du RAG est réalisée (similarité TF-IDF), sans génération, ce qui garde un coût par requête (c) quasi nul.

## Données nécessaires et leur origine (obligatoire)

`data/base_connaissances.csv`, rédigée en anglais par le binôme : au moins trois articles par catégorie (id, categorie, titre, symptomes, etapes séparées par `|`, escalade_si). En complément, la colonne `answer` des tickets d'entraînement Tobi-Bueck permet de montrer la réponse du ticket passé le plus proche.

## Métrique de succès et seuil d'acceptation (obligatoire)

Sur les 12 incidents de test du notebook et le jeu d'or : pour chaque incident correctement classé, l'article proposé est jugé pertinent par le binôme dans au moins 80 % des cas, et aucun article n'est proposé quand la similarité est trop faible (l'incident est alors escaladé).

## Conséquence d'une erreur et validation humaine prévue (obligatoire)

Un article hors sujet fait perdre quelques minutes à l'utilisateur, puis il répond « non résolu » et un ticket pré-rempli part vers un technicien, avec l'article déjà essayé. Les étapes risquées (réinstallation, suppression de données) portent une condition d'escalade dans l'article plutôt que d'être exécutées par l'utilisateur seul.

## Risques éthiques ou de confidentialité (obligatoire)

Les réponses de tickets passés peuvent contenir des noms ou des détails internes : on n'affiche que des extraits de tickets fictifs et publics, et la base interne ne contient aucun mot de passe ni donnée personnelle. Les étapes ne doivent jamais demander à l'utilisateur de communiquer son mot de passe.

## Approche écartée et pourquoi (facultatif)

Un modèle génératif seul est écarté : il inventerait des procédures plausibles mais non validées. Des règles métier (« catégorie réseau → article 1 ») ne sauraient pas départager plusieurs articles d'une même catégorie selon les symptômes décrits.
