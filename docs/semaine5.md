# Semaine 5 : l'interface, notes du binôme

> Trois questions, quelques phrases chacune, avec ce que nous avons observé (API sur le port 8000, page sur le port 8501).

## Ce que fait la page

Deux onglets, en anglais, comme l'utilisateur et le modèle :

- **Report an incident** : l'utilisateur décrit son incident et clique sur « Get help ». La page appelle `POST /assist` et affiche la catégorie et la confiance, puis le message qui correspond au **motif** de la décision. Si un article est proposé, son titre s'affiche avec ses étapes cochables et la condition d'escalade de l'article. Pour une **solution**, la page demande « Is it solved? » : « Yes » ferme l'incident sans ticket, « No » crée aussitôt un ticket pré-rempli (catégorie, priorité, article déjà essayé). Pour une **escalade**, un bouton « Create the ticket » crée le ticket pré-rempli pour le groupe indiqué par l'API.
- **A file of tickets** : un CSV avec une colonne `text`. Chaque ticket passe par `/assist`, et le tableau reçoit la catégorie, la confiance, la priorité, la décision et l'équipe. La page affiche un résumé par catégorie et le nombre de tickets envoyés à un technicien, et propose le téléchargement de `results.csv`.

Streamlit relance tout le script à chaque clic : la réponse de `/assist` et le ticket sont gardés dans `st.session_state`, sinon cocher une étape effacerait la réponse.

## Mesures

| Contrôle | Essai | Obtenu |
| --- | --- | --- |
| T28 | `python -m pytest -q` | 118 passed, 1 xfailed, 1 failed (l'auteur unique) : 15 tests de plus qu'au TP4 (9 du client, 6 de la page) |
| T29 | la page ouverte | « API ready: tfidf-linearsvc (TP2, models/support.joblib), 21 articles » ; `http://127.0.0.1:8501` répond 200 |
| T30 | « My VPN keeps disconnecting every 10 minutes when I work from home » | Network, 91 %, article « VPN disconnects or does not connect », 5 étapes cochables |
| T30 | « The printer on the second floor shows offline and nothing prints, no rush », puis « No » | Hardware, 91 %, article « Printer offline or not printing » ; « Ticket TCK-96F33B78 created and sent to the Poste de travail team. » (nom du groupe corrigé ensuite, voir plus bas) |
| T31 | « xqzvb wlkptr grombu » | « I don't know: a technician will sort this incident », 18 %, et « Most words of your message are unknown to the agent (it only understands English): a technician will take over. » ; « Create the ticket » : ticket pour le tri |
| T32 | trois espaces ; l'API arrêtée | « Text refused: empty, only spaces, or more than 2000 characters. » ; « API unreachable: start uvicorn api.main:app first. » |
| T33 | `data/incidents_exemple.csv` (8 tickets) | résumé `{'INDETERMINE': 2, 'compte_acces': 1, 'facturation': 1, 'logiciel': 1, 'materiel': 1, 'panne_service': 1, 'reseau': 1}` ; 4 tickets sur 8 vers un technicien ; `results.csv` écrit |

T29 à T32 ont été rejoués avec l'outil de test de Streamlit (`AppTest`) sur la vraie page, branchée sur l'API réelle par HTTP (sans `TestClient`), faute de navigateur dans l'environnement de travail. T33 a été rejoué par les fonctions du client que la page appelle, parce que `AppTest` ne sait pas déposer un fichier. Un essai à la main dans le navigateur reste à faire (voir le journal).

**Défaut trouvé en lisant T30** : la page anglaise annonçait « sent to the Poste de travail team ». Les noms des groupes d'escalade, définis dans `api/model.py` en français, sont affichés à l'utilisateur. Ils sont passés en anglais (Workstation, Network, Triage (L1)…), et les tests ont été mis à jour.

## 1. Pourquoi l'interface n'importe-t-elle jamais `predict()` ni le fichier `.joblib` ?

Parce que la page n'est qu'un client de l'API. Tout ce qu'elle sait de l'API tient dans `ui/client.py`, qui parle HTTP à l'adresse `API_URL` et traduit chaque réponse en `Reponse`. Les décisions restent dans l'API : le seuil d'abstention (0,60), le garde-fou de vocabulaire, la recherche dans la base et les règles d'escalade. La page affiche le motif qu'elle reçoit (`mots_inconnus`, `priorite_haute`…) et ne connaît aucun de ces seuils. Si elle chargeait le modèle elle-même, il faudrait recopier les seuils, la base et les règles de la fiche `cas1`, et ces copies finiraient par diverger. C'est exactement ce que nous avons évité en ajoutant le champ `motif` à `/assist` : la page n'a pas à deviner la décision à partir d'une phrase en français. Un modèle réentraîné ou un article ajouté ne demandent aucun changement de la page. Ses tests remplacent simplement `creer_session` par un `TestClient`.

## 2. Que montre l'interface quand le modèle hésite, et pourquoi est-ce mieux qu'un verdict forcé ?

Pour « xqzvb wlkptr grombu », la page affiche « I don't know: a technician will sort this incident », 18 %, et explique pourquoi : la plupart des mots sont inconnus. Pour un incident ambigu mais en anglais, le message parle d'incertitude sur le type d'incident. Le bouton « Create the ticket » envoie alors l'incident au tri (Triage (L1)) avec la raison en clair pour le technicien. Au TP3, le même charabia recevait `logiciel`, et le message en français « Mon VPN ne se connecte plus » recevait `reseau` à 81 %. L'utilisateur aurait suivi une procédure réseau en croyant à un diagnostic sûr. Avec l'abstention, l'agent de premier niveau ne fait perdre de temps à personne : il passe la main tout de suite, et le ticket arrive déjà qualifié comme « à trier ».

## 3. Que voit l'utilisateur quand l'API tombe ? Et le fichier `data/incidents_exemple.csv` : combien de tickets partent vers un technicien ?

Quand l'API est arrêtée, la page rechargée affiche en haut « API unreachable: start uvicorn api.main:app first. » au lieu d'une trace Python. `sante()` interroge `/health` à chaque réexécution, et le client transforme l'erreur de connexion (`httpx.TransportError`) en message. Les autres pannes ont aussi le leur : trois espaces donnent « Text refused… » (422), un modèle absent donne le message du 503. La page n'interprète jamais un code HTTP elle-même.

Pour `data/incidents_exemple.csv`, **4 tickets sur 8 partent vers un technicien**. Le charabia et le message en français vont au tri (`INDETERMINE`). La double facturation part en escalade : le modèle de démonstration lui donne la priorité `high`. La base de données en panne part aussi, pour sa priorité haute. Les quatre autres (VPN, imprimante, Outlook, compte bloqué) reçoivent une solution pas à pas, avec une confiance de 0,91 à 0,93.
