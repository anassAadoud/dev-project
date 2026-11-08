# Aide-mémoire Git

## Ce que fait Git, en trois phrases

Git enregistre l'état des fichiers à des instants choisis : les commits. L'historique est la suite de ces commits, rien n'y est écrasé, ce qui permet de revenir en arrière et de comparer. GitHub héberge une copie du même dépôt, point de rendez-vous entre les deux membres du binôme.

## Les trois zones

| Zone | Ce qu'elle contient | Comment y entrer |
| --- | --- | --- |
| Dossier de travail | Les fichiers tels qu'ils sont sur le disque | On édite |
| Index (zone d'attente) | Ce qui partira dans le prochain commit | `git add <fichier>` |
| Historique | Les commits, définitifs | `git commit -m "message"` |

`git status` dit où en est chaque fichier. C'est la commande à lancer en cas de doute.

## Les commandes du projet

| Commande | Ce qu'elle fait |
| --- | --- |
| `git config --global user.name "Prénom Nom"` | Définit l'auteur des commits sur ce poste |
| `git init` | Crée le dépôt local (le dossier caché `.git/`) |
| `git add -A` | Met tout en attente, sauf ce qu'exclut `.gitignore` |
| `git commit -m "..."` | Enregistre l'index comme un commit |
| `git branch -M main` | Renomme la branche courante en `main` |
| `git remote add origin <url>` | Enregistre l'adresse GitHub sous le nom `origin` |
| `git push -u origin main` | Envoie `main` vers GitHub et lie les deux |
| `git tag -a tp1 -m "..."` | Étiquette la fin d'un TP |
| `git push origin --tags` | Envoie les étiquettes (un simple `git push` ne le fait pas) |
| `git pull` | Récupère les commits de l'autre membre et les fusionne |
| `git log --oneline` | Historique compact |
| `git shortlog -sn --all` | Nombre de commits par auteur |
| `git mv <ancien> <nouveau>` | Déplace un fichier en gardant son historique (TP6) |

## Résoudre un conflit sur README.md

Après `git pull`, le fichier contient les marqueurs `<<<<<<<`, `=======`, `>>>>>>>`. Gardez les deux lignes du tableau, supprimez les marqueurs, puis `git add README.md`, `git commit`, `git push`.

## Trois règles

1. `git status` avant chaque commit, et lire la sortie.
2. `git pull` avant chaque `git push`.
3. Ne jamais commiter ce qui se reconstruit par une commande : `.venv/`, `models/*.joblib`, les données générées, `tickets/`, `graphify-out/`.
