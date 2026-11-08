"""Client HTTP de l'API (TP5) : tout ce que l'interface sait de l'API passe par ce module.

L'interface n'importe jamais predict() ni le fichier .joblib : elle envoie des requêtes à
l'API du TP3, corrigée au TP4, et traduit chaque réponse en message pour l'utilisateur.
Les messages sont en anglais (l'application l'est côté utilisateur) ; le code reste en français.
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
}
INJOIGNABLE = "API unreachable: start uvicorn api.main:app first."
REFUS = "Text refused: empty, only spaces, or more than 2000 characters."
SANS_MODELE = "Model not loaded: run python src/train.py, then restart the API."


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


def creer_session() -> httpx.Client:
    """La connexion à l'API. Les tests la remplacent par un client en mémoire."""
    return httpx.Client(base_url=API_URL, timeout=10)


def _erreur(r: httpx.Response) -> Reponse:
    """Traduit un code d'erreur de l'API en message pour l'utilisateur."""
    if r.status_code == 422:
        return Reponse(False, message=REFUS)
    if r.status_code == 503:
        return Reponse(False, message=SANS_MODELE)
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
