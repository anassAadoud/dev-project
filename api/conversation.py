"""La politique de conversation de l'agent (TP5.1) : répondre d'abord, le ticket en dernier.

Le diagnostic du TP5.1 (src/bilan_tickets.py) a montré que l'agent créait un ticket pour
8 incidents sur 20 que la base sait régler : dès que le modèle hésitait, que la priorité
était haute, ou au premier « No ». Les règles sont maintenant :

1. Jamais de ticket au premier message : l'agent répond, propose les étapes d'un article,
   puis demande si c'est résolu.
2. Pas résolu : il propose un autre article, ou pose une question de précision.
3. Modèle hésitant (INDETERMINE) : une question de précision, avec les boutons de catégories.
4. Le ticket n'est proposé qu'après MAX_TENTATIVES tentatives sans succès, quand l'utilisateur
   le demande, ou pour un cas critique (sécurité, panne générale). Il est toujours confirmé
   par l'utilisateur avant d'être créé.
5. Un seul ticket par conversation, pré-rempli : résumé, catégorie, étapes déjà essayées.

Une tentative sans succès est un article « pas résolu », ou une question de précision qui n'a
mené à aucun article. Ce module ne connaît ni le modèle, ni la base, ni le stockage : ils lui
sont passés par `outils` (le SupportClassifier de api/model.py, ou un faux dans les tests).
"""
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any, Protocol, TypedDict

from api.schemas import Action, Categorie, Code, Label, Phase, Priorite, Source

MAX_TENTATIVES = 2
SEUIL_VOCABULAIRE = 0.50  # la même valeur que api/model.py (vérifié par un test) : sous ce seuil, « reformuler »
CRITIQUES: set[str] = {"securite", "panne_service"}
# Une demande explicite d'un humain, dans le texte de l'utilisateur.
DEMANDE_HUMAIN = re.compile(
    r"\b(open|create|raise|need|want|log|file)\b[^.!?]{0,25}\b(ticket|technician)\b"
    r"|\b(talk|speak)\b[^.!?]{0,15}\b(human|person|technician|someone)\b"
    r"|\b(real person|human agent)\b",
    re.IGNORECASE,
)
# Pourquoi un ticket est proposé, en clair pour le technicien (le ticket garde cette raison).
RAISONS: dict[str, str] = {
    "critique": "cas critique (sécurité ou panne générale) : ticket confirmé par l'utilisateur",
    "deux_essais": f"non résolu après {MAX_TENTATIVES} tentatives de l'agent",
    "demande": "ticket demandé par l'utilisateur",
}


class ActionRefusee(ValueError):
    """L'action n'a pas de sens à ce point de la conversation (l'API répond 409)."""


class Essai(TypedDict):
    """Un article proposé que l'utilisateur a déclaré « pas résolu »."""

    article_id: str
    titre: str
    etapes_faites: list[str]


class Tour(TypedDict):
    tour: int
    action: Action
    code: Code
    le: str


class Conversation(TypedDict):
    """L'état complet d'une conversation, sauvegardé après chaque tour."""

    id: str
    textes: list[str]
    label: Label
    score: float
    priorite: Priorite
    connus: float
    source: Source
    categorie: Categorie | None
    categorie_choisie: bool
    article: dict | None
    essais: list[Essai]
    tentatives: int
    precision_demandee: bool
    critique_propose: bool
    phase: Phase
    code: Code
    tours: list[Tour]
    ticket_id: str | None


class Outils(Protocol):
    """Ce dont la politique a besoin : le modèle, la base de connaissances, la création du ticket."""

    def predict(self, text: str) -> Mapping[str, Any]: ...

    def chercher(self, text: str, categorie: str, exclus: Iterable[str]) -> dict | None: ...

    def creer_ticket_conversation(self, conv: Conversation) -> dict: ...


def demande_humain(texte: str) -> bool:
    """L'utilisateur demande un ticket ou un technicien avec ses mots (« please open a ticket »)."""
    return bool(DEMANDE_HUMAIN.search(texte))


def texte_complet(conv: Conversation) -> str:
    """Tout ce que l'utilisateur a écrit : la précision complète le premier message."""
    return " ".join(conv["textes"])


def resumer(conv: Conversation, longueur: int = 160) -> str:
    """Le résumé du ticket : le premier message, puis les précisions, en une ligne courte."""
    premier = conv["textes"][0].strip()
    resume = premier if len(premier) <= longueur else premier[: longueur - 1].rstrip() + "…"
    if len(conv["textes"]) > 1:
        resume += f" (+{len(conv['textes']) - 1} detail(s): {conv['textes'][-1].strip()[:80]})"
    return resume


def actions_possibles(conv: Conversation) -> list[Action]:
    """Les réponses que la page peut proposer à l'utilisateur maintenant."""
    phase = conv["phase"]
    if phase == "solution":
        return ["resolu", "pas_resolu", "demander_ticket", "message"]
    if phase == "precision":
        return ["categorie", "message", "demander_ticket"]
    if phase == "proposition_ticket":
        choix: list[Action] = ["confirmer_ticket", "refuser_ticket"]
        return [*choix, "resolu", "message"] if conv["article"] else [*choix, "message"]
    return []  # résolue ou ticket créé : la conversation est terminée


def nouvelle(identifiant: str) -> Conversation:
    return {"id": identifiant, "textes": [], "label": "INDETERMINE", "score": 0.0, "priorite": "low", "connus": 0.0, "source": "aucune",
            "categorie": None, "categorie_choisie": False, "article": None, "essais": [], "tentatives": 0,
            "precision_demandee": False, "critique_propose": False, "phase": "precision", "code": "choisir_categorie",
            "tours": [], "ticket_id": None}


def _classer(conv: Conversation, outils: Outils) -> None:
    """Le modèle relit tout le texte, sauf si l'utilisateur a choisi la catégorie lui-même."""
    p = outils.predict(texte_complet(conv))
    conv["label"], conv["score"], conv["priorite"], conv["connus"] = p["label"], p["score"], p["priorite"], p["connus"]
    conv["source"] = p.get("source", "modele")
    if not conv["categorie_choisie"]:
        conv["categorie"] = None if p["label"] == "INDETERMINE" else p["label"]


def _proposer_ticket(conv: Conversation, code: Code) -> None:
    conv["phase"], conv["code"] = "proposition_ticket", code


def _proposer_solution(conv: Conversation, outils: Outils) -> None:
    """Un article pas encore essayé ; sinon une question de précision ; après MAX_TENTATIVES, le ticket."""
    assert conv["categorie"] is not None
    exclus = [e["article_id"] for e in conv["essais"]]
    article = outils.chercher(texte_complet(conv), conv["categorie"], exclus)
    if article is not None:
        conv["article"], conv["phase"] = article, "solution"
        conv["code"] = "autre_solution" if conv["essais"] else "solution"
        conv["precision_demandee"] = False
        return
    conv["article"] = None
    if conv["precision_demandee"]:  # la précision demandée n'a mené à aucun article : tentative perdue
        conv["tentatives"] += 1
    if conv["tentatives"] >= MAX_TENTATIVES:
        _proposer_ticket(conv, "deux_essais")
        return
    conv["precision_demandee"], conv["phase"], conv["code"] = True, "precision", "question_precision"


def _repondre(conv: Conversation, outils: Outils) -> None:
    """Après un message ou un choix de catégorie : critique, hésitation, ou solution."""
    if conv["categorie"] is None:
        conv["article"], conv["precision_demandee"], conv["phase"] = None, True, "precision"
        if conv.get("source") == "hors_sujet":
            conv["code"] = "hors_sujet"
        else:
            conv["code"] = "reformuler" if conv["connus"] < SEUIL_VOCABULAIRE else "choisir_categorie"
        return
    if conv["categorie"] in CRITIQUES and not conv["critique_propose"]:
        # Les étapes de l'article s'affichent quand même : l'utilisateur agit en attendant le technicien.
        conv["critique_propose"] = True
        conv["article"] = outils.chercher(texte_complet(conv), conv["categorie"], [])
        _proposer_ticket(conv, "critique")
        return
    _proposer_solution(conv, outils)


def _verifier(conv: Conversation, action: Action) -> None:
    if action not in actions_possibles(conv):
        if conv["phase"] == "ticket":
            raise ActionRefusee(f"un seul ticket par conversation : {conv['ticket_id']} existe déjà")
        raise ActionRefusee(f"action « {action} » impossible quand la conversation est en phase « {conv['phase']} »")


def avancer(conv: Conversation, action: Action, outils: Outils, texte: str | None = None,
            categorie: Categorie | None = None, etapes_faites: Iterable[str] = ()) -> Conversation:
    """Un tour de conversation : applique l'action de l'utilisateur, renvoie le nouvel état."""
    premier = not conv["tours"]
    if premier and action != "message":
        raise ActionRefusee("une conversation commence par un message")
    if not premier:
        _verifier(conv, action)

    if action == "message":
        if not texte or not texte.strip():
            raise ActionRefusee("un message demande un texte")
        conv["textes"].append(texte.strip())
        _classer(conv, outils)
        if demande_humain(texte):
            if conv["categorie"] is not None and conv["article"] is None:
                conv["article"] = outils.chercher(texte_complet(conv), conv["categorie"], [])
            _proposer_ticket(conv, "demande")
        else:
            _repondre(conv, outils)
    elif action == "categorie":
        if categorie is None:
            raise ActionRefusee("choisir une catégorie demande la catégorie")
        conv["categorie"], conv["categorie_choisie"] = categorie, True
        _repondre(conv, outils)
    elif action == "resolu":
        conv["phase"], conv["code"] = "resolu", "resolu"
    elif action == "pas_resolu":
        article = conv["article"]
        assert article is not None
        conv["essais"].append({"article_id": article["id"], "titre": article["titre"],
                               "etapes_faites": [e for e in etapes_faites if e]})
        conv["tentatives"] += 1
        if conv["tentatives"] >= MAX_TENTATIVES:
            conv["article"] = None
            _proposer_ticket(conv, "deux_essais")
        else:
            _proposer_solution(conv, outils)
    elif action == "demander_ticket":
        _proposer_ticket(conv, "demande")
    elif action == "confirmer_ticket":
        ticket = outils.creer_ticket_conversation(conv)
        conv["ticket_id"], conv["phase"], conv["code"] = ticket["id"], "ticket", "ticket_cree"
    else:  # refuser_ticket : l'utilisateur continue avec l'agent
        conv["phase"] = "solution" if conv["article"] else "precision"
        conv["code"] = "ticket_refuse"

    conv["tours"].append({"tour": len(conv["tours"]) + 1, "action": action, "code": conv["code"],
                          "le": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    return conv


def raison_du_ticket(conv: Conversation) -> str:
    """La raison du ticket, d'après le dernier code qui l'a proposé."""
    for tour in reversed(conv["tours"]):
        if tour["code"] in RAISONS:
            return RAISONS[tour["code"]]
    return RAISONS["demande"]
