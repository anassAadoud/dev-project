#!/usr/bin/env python
"""Bilan des tickets sur 30 conversations (TP5.1) : combien de tickets l'agent crée, et pourquoi.

Chaque ligne de data/conversations_30.csv décrit un incident et l'utilisateur qui l'écrit :
  - scenario « resolu » : un des articles de articles_ok règle le problème ;
  - « non_resolu » : aucun article ne le règle ;
  - « demande » : l'utilisateur veut un technicien ;
  - « critique » : sécurité ou panne générale.
Un utilisateur simulé répond à l'agent : « résolu » si l'article proposé est dans articles_ok,
« pas résolu » sinon, sa phrase de précision si on lui pose une question, la bonne catégorie
si on lui montre les boutons, et « oui » quand on lui propose un ticket.

Attendu : aucun ticket pour un incident résolu, un ticket pour chacun des autres.

Usage, depuis la racine du dépôt, modèle entraîné :
  python src/bilan_tickets.py
Les chiffres affichés vont dans docs/semaine5.1.md.
"""
import csv
import logging
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
CONVERSATIONS = RACINE / "data" / "conversations_30.csv"


def lire_conversations() -> list[dict[str, str]]:
    with CONVERSATIONS.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ticket_attendu(ligne: dict[str, str]) -> int:
    """Un ticket pour tout ce qui n'est pas réglé par un article de la base."""
    return 0 if ligne["scenario"] == "resolu" else 1


def avant(ligne: dict[str, str], clf) -> tuple[int, str]:
    """La page du TP5 : une escalade de /assist propose le ticket ; « No » le crée aussitôt."""
    aide = clf.assist(ligne["text"])
    if aide["decision"] == "escalade":
        return 1, aide["motif"]
    ok = set(ligne["articles_ok"].split()) if ligne["articles_ok"] else set()
    if ligne["scenario"] == "resolu" and aide["article"] and aide["article"]["id"] in ok:
        return 0, "résolu au premier article"
    return 1, "« No » au premier article : ticket créé aussitôt"


def main() -> int:
    sys.path.insert(0, str(RACINE))
    from api.model import load_model

    logging.disable(logging.INFO)
    lignes = lire_conversations()
    clf = load_model()

    causes: Counter[str] = Counter()
    tickets = inutiles = 0
    for ligne in lignes:
        n, cause = avant(ligne, clf)
        tickets += n
        inutiles += n > ticket_attendu(ligne)
        causes[cause] += 1
        print(f"avant  {n} ticket  {cause:<48} {ligne['scenario']:<10} {ligne['text'][:55]}")

    resolubles = sum(1 for ligne in lignes if ligne["scenario"] == "resolu")
    print(f"\nAvant (TP5) : {tickets} tickets sur {len(lignes)} conversations ({tickets / len(lignes):.0%}), "
          f"dont {inutiles} pour un incident que la base sait régler ({resolubles} incidents résolubles)")
    print("Causes : " + ", ".join(f"{k} {v}" for k, v in causes.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
