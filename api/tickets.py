"""Les tickets : création, lecture, suivi du statut (TP3, suivi au TP5.1).

Ils sont rangés par api/stockage.py dans tickets.jsonl (chemin : variable SUPPORT_TICKETS,
sinon tickets/tickets.jsonl à la racine du dépôt). Chaque changement de statut ajoute une
version du ticket, avec un événement dans son historique.
"""
import uuid
from datetime import datetime, timezone

from api import stockage
from api.stockage import chemin_tickets

__all__ = ["chemin_tickets", "creer", "lire", "lister", "mettre_a_jour", "pour_conversation"]


def maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def creer(champs: dict) -> dict:
    """Ajoute un ticket ouvert et le renvoie, avec son identifiant, sa date et son premier événement."""
    le = maintenant()
    ticket = {"id": f"TCK-{uuid.uuid4().hex[:8].upper()}", "cree_le": le, "statut": "ouvert", **champs,
              "historique": [{"le": le, "statut": "ouvert", "commentaire": champs.get("raison")}]}
    return stockage.ajouter("tickets", ticket)


def lire(identifiant: str) -> dict | None:
    """Le ticket portant cet identifiant (sa version actuelle), ou None."""
    return stockage.lire("tickets", identifiant)


def lister() -> list[dict]:
    return stockage.tous("tickets")


def pour_conversation(conversation_id: str) -> dict | None:
    """Le ticket déjà créé pour cette conversation, s'il existe : il ne peut y en avoir qu'un."""
    return next((t for t in lister() if t.get("conversation_id") == conversation_id), None)


def mettre_a_jour(identifiant: str, statut: str, commentaire: str | None = None,
                  resolution: str | None = None) -> dict | None:
    """Change le statut du ticket et garde la trace du changement ; None si le ticket n'existe pas."""
    ticket = lire(identifiant)
    if ticket is None:
        return None
    ticket["statut"] = statut
    if resolution:
        ticket["resolution"] = resolution
    ticket["historique"] = [*ticket.get("historique", []),
                            {"le": maintenant(), "statut": statut, "commentaire": commentaire}]
    return stockage.ajouter("tickets", ticket)
