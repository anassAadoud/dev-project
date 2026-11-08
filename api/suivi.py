"""Le suivi de l'agent (TP5.1) : les avis 👍/👎 et les chiffres de la page de statistiques.

Le chiffre principal est le taux de résolution sans ticket : parmi les conversations
terminées, la part que l'agent a réglée seul. Une conversation en cours ne compte pas
encore : elle n'est ni un succès ni un échec.
"""
import uuid
from collections import Counter
from datetime import datetime, timezone

from api import stockage, tickets


def ajouter_avis(conversation: dict, tour: int, utile: bool, commentaire: str | None) -> dict:
    """Enregistre l'avis sur une réponse ; refuse un tour qui n'existe pas dans la conversation."""
    tours = {t["tour"]: t for t in conversation["tours"]}
    if tour not in tours:
        raise KeyError(tour)
    avis = {"id": f"AVS-{uuid.uuid4().hex[:8].upper()}", "le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "conversation_id": conversation["id"], "tour": tour, "utile": utile, "commentaire": commentaire,
            "code": tours[tour]["code"]}
    return stockage.ajouter("feedback", avis)


def statistiques() -> dict:
    conversations = stockage.tous("conversations")
    resolues = sum(1 for c in conversations if c["phase"] == "resolu" and not c.get("ticket_id"))
    avec_ticket = sum(1 for c in conversations if c.get("ticket_id"))
    terminees = resolues + avec_ticket
    avis = stockage.tous("feedback")
    return {
        "conversations": len(conversations),
        "resolues_sans_ticket": resolues,
        "avec_ticket": avec_ticket,
        "en_cours": len(conversations) - terminees,
        "taux_resolution_sans_ticket": round(resolues / terminees, 3) if terminees else None,
        "categories": dict(Counter(c.get("categorie") or "INDETERMINE" for c in conversations).most_common()),
        "tickets_par_statut": dict(Counter(t["statut"] for t in tickets.lister()).most_common()),
        "avis_utiles": sum(1 for a in avis if a["utile"]),
        "avis_pas_utiles": sum(1 for a in avis if not a["utile"]),
        "tentatives_moyennes": (round(sum(c["tentatives"] for c in conversations) / len(conversations), 2)
                                if conversations else None),
    }
