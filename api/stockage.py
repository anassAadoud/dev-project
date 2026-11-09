"""Le stockage de l'agent (TP5.1) : des fichiers JSON Lines, hors de Git, une ligne par version.

Tickets, conversations et avis (utile ou pas) sont rangés dans le même dossier : celui du fichier
SUPPORT_TICKETS si la variable est définie (les tests la redirigent vers un dossier temporaire),
sinon tickets/ à la racine du dépôt. Un objet modifié est réécrit à la fin du fichier : la
dernière ligne qui porte son identifiant est sa version actuelle, et les précédentes font son
historique. C'est simple, sans base de données, et suffisant pour un agent de premier niveau.
"""
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("support_api")

RACINE = Path(__file__).resolve().parents[1]
NOMS = {"tickets", "conversations", "feedback"}


def chemin_tickets() -> Path:
    """SUPPORT_TICKETS si elle est définie, sinon tickets/tickets.jsonl dans le dépôt."""
    return Path(os.environ.get("SUPPORT_TICKETS") or RACINE / "tickets" / "tickets.jsonl")


def chemin(nom: str) -> Path:
    """Le fichier d'une collection : tickets.jsonl, conversations.jsonl ou feedback.jsonl."""
    if nom not in NOMS:
        raise ValueError(f"collection inconnue : {nom}")
    tickets = chemin_tickets()
    return tickets if nom == "tickets" else tickets.with_name(f"{nom}.jsonl")


def ajouter(nom: str, objet: dict) -> dict:
    """Écrit une nouvelle version de l'objet à la fin de la collection."""
    fichier = chemin(nom)
    fichier.parent.mkdir(parents=True, exist_ok=True)
    with fichier.open("a", encoding="utf-8") as f:
        f.write(json.dumps(objet, ensure_ascii=False) + "\n")
    return objet


def tous(nom: str) -> list[dict]:
    """La version actuelle de chaque objet, dans l'ordre de leur première apparition."""
    fichier = chemin(nom)
    if not fichier.exists():
        return []
    actuels: dict[str, dict] = {}
    with fichier.open(encoding="utf-8", errors="replace") as f:
        for numero, ligne in enumerate(f, start=1):
            if not ligne.strip():
                continue
            try:  # TP5.2 : une ligne abîmée (écriture coupée, édition à la main) n'empêche pas de lire les autres
                objet = json.loads(ligne)
                actuels[objet["id"]] = objet
            except (json.JSONDecodeError, KeyError, TypeError):
                logger.warning("%s, ligne %d illisible : ignorée", fichier.name, numero)
    return list(actuels.values())


def lire(nom: str, identifiant: str) -> dict | None:
    """La version actuelle de l'objet, ou None."""
    return next((o for o in tous(nom) if o["id"] == identifiant), None)
