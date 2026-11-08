# Fiche de cadrage : Escalade des incidents vers un technicien

> Remplir chaque rubrique en une à trois phrases. Les rubriques marquées (obligatoire) sont vérifiées par `pytest`.

## Besoin en une phrase (obligatoire)

Décider, pour chaque incident déjà classé, s'il doit partir tout de suite vers un technicien (et vers quel groupe) ou si l'utilisateur peut d'abord essayer une solution guidée.

## Utilisateur final (obligatoire)

L'agent de support lui-même applique la décision ; les techniciens de niveau 1 et 2 reçoivent les tickets escaladés, et le responsable du support relit et ajuste les règles.

## Approche retenue (obligatoire)

Cocher une seule case :

- [x] Règles métier
- [ ] Machine learning
- [ ] RAG
- [ ] Modèle génératif seul

## Justification (obligatoire, citer au moins deux critères de la grille : (a) données étiquetées, (b) vérifiabilité, (c) coût par requête, (d) conséquence d'une erreur)

(b) Une escalade doit pouvoir être expliquée au technicien et à l'utilisateur : « priorité haute », « catégorie sécurité », « le modèle doute » sont des règles lisibles, qu'on teste une par une. (d) Un incident urgent laissé à l'utilisateur coûte cher (service bloqué, faille non traitée) : la règle doit être prévisible, pas apprise. (a) Nous n'avons aucun historique étiqueté « escaladé / non escaladé » ; les règles s'appuient sur les sorties des modèles (catégorie, confiance, priorité) et sur la réponse de l'utilisateur. (c) Une règle ne coûte rien par requête.

## Données nécessaires et leur origine (obligatoire)

Les sorties des deux modèles du projet (catégorie IT et confiance, priorité low / medium / high), la réponse de l'utilisateur à « Is it solved? », et une table des groupes d'escalade par catégorie (sécurité, réseau, matériel, comptes, facturation, logiciel, panne de service, plus un groupe de tri N1), écrite par le binôme.

## Métrique de succès et seuil d'acceptation (obligatoire)

Sur les 12 incidents de test du notebook et le jeu d'or du TP4 : 100 % des incidents de priorité haute, de catégorie incertaine (`INDETERMINE`) ou déclarés non résolus sont escaladés, et chaque ticket escaladé porte son groupe et sa raison. Les règles sont couvertes par des tests automatiques.

## Conséquence d'une erreur et validation humaine prévue (obligatoire)

Une escalade inutile occupe un technicien quelques minutes ; une escalade manquée laisse un utilisateur bloqué. Dans le doute, la règle escalade. Le technicien qui reçoit le ticket peut le réaffecter à un autre groupe, et l'utilisateur peut toujours demander un ticket même si une solution a été proposée.

## Risques éthiques ou de confidentialité (obligatoire)

Le ticket transmet la description de l'incident, qui peut contenir un nom, une adresse électronique ou un identifiant : on ne stocke que ce qui sert au traitement, hors de Git, et les données de test sont publiques ou fictives. Les règles ne doivent pas défavoriser un utilisateur selon autre chose que l'incident lui-même.

## Approche écartée et pourquoi (facultatif)

Le machine learning est écarté : sans historique d'escalades étiqueté, on ne peut ni l'entraîner ni le mesurer, et une décision apprise serait plus difficile à expliquer au technicien.
