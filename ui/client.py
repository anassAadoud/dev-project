"""Client HTTP de l'API (TP5) : tout ce que l'interface sait de l'API passe par ce module.

L'interface n'importe jamais predict() ni le fichier .joblib : elle envoie des requêtes à
l'API du TP3, corrigée au TP4, et traduit chaque réponse en message pour l'utilisateur.
Les messages sont en anglais (l'application l'est côté utilisateur) ; le code reste en français.

TP5.1 : la conversation (/chat), le suivi des tickets, les avis (utile ou pas) et les statistiques.
L'API renvoie un code par réponse de l'agent ; ce module le traduit (REPLIQUES), comme le motif.
"""
import os
from collections import Counter
from dataclasses import dataclass, field

import httpx

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

# Les catégories du contrat, telles que l'utilisateur les lit.
VERDICTS = {
    "securite": "Security",
    "reseau": "Network",
    "materiel": "Hardware",
    "compte_acces": "Account and access",
    "facturation": "Billing",
    "logiciel": "Software",
    "panne_service": "Service outage",
    "INDETERMINE": "I don't know: a technician will sort this incident",
}
# Le motif de la décision de /assist (règles de la fiche cas1), traduit pour l'utilisateur.
MOTIFS = {
    "mots_inconnus": "Most words of your message are unknown to the agent (it only understands English): "
                     "a technician will take over.",
    "confiance_basse": "The agent is not sure which kind of incident this is: a technician will take over.",
    "priorite_haute": "This looks urgent: a technician will take over right away. "
                      "You can try the steps below while you wait.",
    "sans_article": "No article of the knowledge base matches this incident: a technician will take over.",
    "article_escalade": "This kind of incident is always handled by a technician. "
                        "You can try the steps below while you wait.",
    "solution": "Try these steps, then tell us if the problem is solved.",
    "critique": "This looks critical: a technician will take over. You can try the steps below while you wait.",
}
# Ce que l'agent dit à chaque code de /chat (TP5.1).
REPLIQUES = {
    "solution": "Here is what usually fixes this. Try these steps, then tell me if it is solved.",
    "autre_solution": "Let's try something else. Here is another solution:",
    "question_precision": "I need a bit more detail to find the right solution. What exactly happens: which device "
                          "or application, and is there an error message? You can also pick the kind of problem below.",
    "choisir_categorie": "I'm not sure which kind of problem this is. Pick it below, or describe it in a bit more detail.",
    "reformuler": "I don't understand most of these words (I only understand English). Describe the problem again "
                  "in English, or pick the kind of problem below.",
    "critique": "This looks critical. Do the steps below right away. I suggest sending it to a technician now: "
                "shall I create a ticket?",
    "deux_essais": "I'm sorry, my solutions did not fix it. Shall I create a ticket for a technician? "
                   "It will include what you already tried.",
    "demande": "Of course. Shall I create a ticket for a technician? It will include a summary of your problem.",
    "resolu": "Great, glad it's fixed! No ticket was needed.",
    "ticket_cree": "Your ticket is created and sent to a technician. You can follow it in the Track a ticket tab.",
    "ticket_refuse": "OK, no ticket for now. Tell me more, or try the steps again.",
}
# Qui a choisi la catégorie (TP5.1) : le modèle, ou la base de connaissances quand le modèle hésite.
SOURCES = {"modele": "model", "base": "knowledge base", "aucune": "nobody (sent to triage)"}
# Les statuts d'un ticket, tels que l'utilisateur les lit.
STATUTS = {"ouvert": "Open", "en_cours": "In progress", "resolu": "Resolved", "ferme": "Closed"}
INJOIGNABLE = "API unreachable: start uvicorn api.main:app first."
REFUS = "Text refused: empty, only spaces, or more than 2000 characters."
SANS_MODELE = "Model not loaded: run python src/train.py, then restart the API."
INTROUVABLE = "Not found: check the identifier."
HORS_DE_PROPOS = "This is not possible at this point of the conversation."


@dataclass
class Reponse:
    """Ce que l'interface affiche : un résultat, ou un message d'erreur lisible."""

    ok: bool
    label: str | None = None
    score: float | None = None
    priorite: str | None = None
    decision: str | None = None
    motif: str | None = None
    groupe: str | None = None
    article: dict | None = None
    ticket: dict | None = None
    message: str = ""
    corps: dict = field(default_factory=dict)
    # TP5.1 : la conversation
    conversation_id: str | None = None
    tour: int | None = None
    phase: str | None = None
    code: str | None = None
    choix: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)


def creer_session() -> httpx.Client:
    """La connexion à l'API. Les tests la remplacent par un client en mémoire."""
    return httpx.Client(base_url=API_URL, timeout=10)


def _erreur(r: httpx.Response) -> Reponse:
    """Traduit un code d'erreur de l'API en message pour l'utilisateur."""
    if r.status_code == 422:
        return Reponse(False, message=REFUS)
    if r.status_code == 503:
        return Reponse(False, message=SANS_MODELE)
    if r.status_code == 404:
        return Reponse(False, message=INTROUVABLE)
    if r.status_code == 409:
        return Reponse(False, message=HORS_DE_PROPOS)
    return Reponse(False, message=f"Internal error of the API ({r.status_code}).")


def sante(session: httpx.Client) -> Reponse:
    try:
        r = session.get("/health")
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code == 200:
        corps = r.json()
        return Reponse(True, message=f"{corps['model']}, {corps['articles']} articles")
    return _erreur(r)


def predire(session: httpx.Client, texte: str) -> Reponse:
    """POST /predict : la catégorie, la confiance et la priorité."""
    try:
        r = session.post("/predict", json={"text": texte})
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 200:
        return _erreur(r)
    corps = r.json()
    return Reponse(True, label=corps["label"], score=corps["score"], priorite=corps["priorite"], corps=corps)


def assister(session: httpx.Client, texte: str) -> Reponse:
    """POST /assist : la catégorie, l'article proposé et la décision de l'API."""
    try:
        r = session.post("/assist", json={"text": texte})
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 200:
        return _erreur(r)
    c = r.json()
    return Reponse(True, label=c["label"], score=c["score"], priorite=c["priorite"], decision=c["decision"],
                   motif=c["motif"], groupe=c["groupe"], article=c["article"], message=MOTIFS[c["motif"]], corps=c)


def creer_ticket(session: httpx.Client, texte: str, aide: Reponse | None = None, raison: str = "") -> Reponse:
    """POST /tickets : un ticket pré-rempli avec ce que /assist a trouvé, s'il a été appelé."""
    champs: dict = {"text": texte, "raison": raison or None}
    if aide is not None and aide.ok:
        champs |= {"label": aide.label, "priorite": aide.priorite,
                   "article_id": aide.article["id"] if aide.article else None}
    try:
        r = session.post("/tickets", json=champs)
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 201:
        return _erreur(r)
    ticket = r.json()
    return Reponse(True, label=ticket["label"], priorite=ticket["priorite"], groupe=ticket["groupe"], ticket=ticket,
                   message=f"Ticket {ticket['id']} created and sent to the {ticket['groupe']} team.")


def assister_lot(session: httpx.Client, textes: list[str]) -> list[Reponse]:
    return [assister(session, texte) for texte in textes]


def resumer(reponses: list[Reponse]) -> dict[str, int]:
    """Nombre d'incidents par catégorie ; les refus et les erreurs sont comptés à part."""
    compte = Counter((r.label or "?") if r.ok else "REFUSED OR ERROR" for r in reponses)
    return dict(sorted(compte.items()))


def a_escalader(reponses: list[Reponse]) -> int:
    """Combien d'incidents du lot partent vers un technicien."""
    return sum(1 for r in reponses if r.ok and r.decision == "escalade")


# --- TP5.1 : la conversation, le suivi, les avis, les statistiques ---

def discuter(session: httpx.Client, action: str = "message", conversation_id: str | None = None,
             texte: str | None = None, categorie: str | None = None, etapes_faites: list[str] | None = None) -> Reponse:
    """POST /chat : un tour de conversation. Sans conversation_id, une nouvelle conversation commence."""
    corps = {"conversation_id": conversation_id, "action": action, "text": texte, "categorie": categorie,
             "etapes_faites": etapes_faites or []}
    try:
        r = session.post("/chat", json=corps)
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 200:
        return _erreur(r)
    c = r.json()
    return Reponse(True, label=c["label"], score=c["score"], priorite=c["priorite"], article=c["article"],
                   ticket=c["ticket"], message=REPLIQUES[c["code"]], corps=c, conversation_id=c["conversation_id"],
                   tour=c["tour"], phase=c["phase"], code=c["code"], choix=c["choix"], categories=c["categories"],
                   groupe=(c["ticket"] or {}).get("groupe"))


def donner_avis(session: httpx.Client, conversation_id: str, tour: int, utile: bool) -> Reponse:
    """POST /feedback : la réponse de l'agent était-elle utile ?"""
    try:
        r = session.post("/feedback", json={"conversation_id": conversation_id, "tour": tour, "utile": utile})
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 201:
        return _erreur(r)
    return Reponse(True, message="Thanks for your feedback!", corps=r.json())


def suivre_ticket(session: httpx.Client, identifiant: str) -> Reponse:
    """GET /tickets/{id} : le statut et l'historique du ticket."""
    try:
        r = session.get(f"/tickets/{identifiant.strip().upper()}")
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 200:
        return _erreur(r)
    ticket = r.json()
    return Reponse(True, label=ticket["label"], priorite=ticket["priorite"], groupe=ticket["groupe"], ticket=ticket,
                   message=f"Ticket {ticket['id']}: {STATUTS[ticket['statut']]}", corps=ticket)


def mettre_a_jour_ticket(session: httpx.Client, identifiant: str, statut: str, commentaire: str = "",
                         resolution: str = "") -> Reponse:
    """PATCH /tickets/{id} : le technicien fait avancer le ticket."""
    try:
        r = session.patch(f"/tickets/{identifiant}", json={"statut": statut, "commentaire": commentaire or None,
                                                           "resolution": resolution or None})
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 200:
        return _erreur(r)
    ticket = r.json()
    return Reponse(True, ticket=ticket, message=f"Ticket {ticket['id']} is now {STATUTS[ticket['statut']]}.",
                   corps=ticket)


def statistiques(session: httpx.Client) -> Reponse:
    """GET /stats : les chiffres de la page de statistiques."""
    try:
        r = session.get("/stats")
    except httpx.TransportError:
        return Reponse(False, message=INJOIGNABLE)
    if r.status_code != 200:
        return _erreur(r)
    return Reponse(True, corps=r.json())
