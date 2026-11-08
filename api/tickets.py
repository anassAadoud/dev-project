"""Le stockage des tickets : un fichier JSON Lines, une ligne par ticket, hors de Git.

Le chemin vient de la variable d'environnement SUPPORT_TICKETS, sinon tickets/tickets.jsonl
à la racine du dépôt. Les tests le redirigent vers un dossier temporaire.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]


def chemin_tickets() -> Path:
    """SUPPORT_TICKETS si elle est définie, sinon tickets/tickets.jsonl dans le dépôt."""
    return Path(os.environ.get("SUPPORT_TICKETS") or RACINE / "tickets" / "tickets.jsonl")


def creer(champs: dict) -> dict:
    """Ajoute un ticket ouvert et le renvoie, avec son identifiant et sa date."""
    ticket = {"id": f"TCK-{uuid.uuid4().hex[:8].upper()}",
              "cree_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "statut": "ouvert", **champs}
    chemin = chemin_tickets()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ticket, ensure_ascii=False) + "\n")
    return ticket


def lire(identifiant: str) -> dict | None:
    """Le ticket portant cet identifiant, ou None."""
    chemin = chemin_tickets()
    if not chemin.exists():
        return None
    with chemin.open(encoding="utf-8") as f:
        for ligne in f:
            if ligne.strip():
                ticket = json.loads(ligne)
                if ticket["id"] == identifiant:
                    return ticket
    return None
