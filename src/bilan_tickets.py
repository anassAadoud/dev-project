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
import os
import sys
import tempfile
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


MAX_TOURS = 12


def apres(ligne: dict[str, str], client) -> tuple[int, int, str, list[str]]:
    """La conversation du TP5.1 (/chat), avec l'utilisateur simulé. Renvoie le nombre de tickets,
    le nombre de tours, la façon dont elle s'est terminée et la suite des codes de l'agent."""
    ok = set(ligne["articles_ok"].split()) if ligne["articles_ok"] else set()
    r = client.post("/chat", json={"text": ligne["text"]}).json()
    codes, precise, demande, tickets = [r["code"]], False, False, set()
    if r["phase"] == "proposition_ticket" and r["tour"] == 1 and r["ticket"]:
        raise AssertionError("ticket créé dès le premier message")
    for _ in range(MAX_TOURS):
        if r["phase"] in {"resolu", "ticket"}:
            break
        if ligne["scenario"] == "demande" and not demande and "demander_ticket" in r["choix"]:
            action, demande = {"action": "demander_ticket"}, True
        elif r["phase"] == "proposition_ticket":
            action = ({"action": "resolu"} if r["article"] and r["article"]["id"] in ok
                      else {"action": "confirmer_ticket"})
        elif r["phase"] == "solution":
            if r["article"]["id"] in ok:
                action = {"action": "resolu"}
            else:
                action = {"action": "pas_resolu", "etapes_faites": r["article"]["etapes"][:2]}
        elif not precise and r["code"] == "question_precision":
            action, precise = {"action": "message", "text": ligne["precision"]}, True
        else:  # boutons de catégories : l'utilisateur choisit la bonne
            action = {"action": "categorie", "categorie": ligne["attendu"]}
        r = client.post("/chat", json={"conversation_id": r["conversation_id"], **action}).json()
        codes.append(r["code"])
        if r.get("ticket"):
            tickets.add(r["ticket"]["id"])
    fin = "résolu sans ticket" if r["phase"] == "resolu" else ("ticket" if tickets else f"inachevé ({r['phase']})")
    return len(tickets), len(codes), fin, codes


def main() -> int:
    sys.path.insert(0, str(RACINE))
    from fastapi.testclient import TestClient

    from api.main import app
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

    # Après (TP5.1) : les tickets vont dans un dossier temporaire, jamais dans tickets/ du dépôt.
    print()
    fins: Counter[str] = Counter()
    tickets_apres = ecarts = tours = 0
    with tempfile.TemporaryDirectory() as dossier:
        os.environ["SUPPORT_TICKETS"] = str(Path(dossier) / "tickets.jsonl")
        with TestClient(app) as client:
            for ligne in lignes:
                n, nb_tours, fin, codes = apres(ligne, client)
                tickets_apres += n
                tours += nb_tours
                ecarts += n != ticket_attendu(ligne)
                fins[fin] += 1
                print(f"après  {n} ticket  {fin:<20} {ligne['scenario']:<10} {ligne['text'][:45]:<45} "
                      f"{' > '.join(codes)}")
    print(f"\nAprès (TP5.1) : {tickets_apres} tickets sur {len(lignes)} conversations "
          f"({tickets_apres / len(lignes):.0%}), attendus {sum(ticket_attendu(ligne) for ligne in lignes)} ; "
          f"écarts à l'attendu : {ecarts} ; {tours / len(lignes):.1f} tours en moyenne")
    print("Fins : " + ", ".join(f"{k} {v}" for k, v in fins.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
