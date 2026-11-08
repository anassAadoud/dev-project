"""Raccord entre l'API, le modèle du TP2 et la base de connaissances.

L'API n'entraîne rien et ne connaît pas scikit-learn : elle appelle predict() du TP2,
qui charge models/support.joblib une seule fois, et chercher() de src/kb.py.
Les règles d'escalade de la fiche cas1 vivent ici : elles sont lisibles et testées.

TP4 : l'API s'abstient (INDETERMINE) au lieu de deviner, dans deux cas : la confiance est
sous SEUIL_ABSTENTION, ou moins de SEUIL_VOCABULAIRE des mots sont connus du modèle.
Les étiquettes du modèle passent par des correspondances explicites, vérifiées au démarrage.

TP5.1 : quand le modèle hésite (confiance sous le seuil) mais connaît les mots, la base de
connaissances donne un second avis : si un article ressemble assez au texte (SEUIL_BASE), sa
catégorie est retenue. Les mots inconnus (autre langue, charabia) vont toujours au tri.

TP5.1 : la conversation (api/conversation.py) utilise ce classifier comme ses outils : le
modèle, la base (articles déjà essayés exclus) et la création du ticket. /assist et ses règles
suivent la même politique que la conversation (decider_tp51) : un fichier de tickets ne doit pas
annoncer un technicien pour un incident que l'agent règle dans la conversation. Les règles du TP4
(decider) restent, pour rejouer la mesure « avant » de src/bilan_tickets.py.
"""
import sys
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import TypedDict

from api import conversation, llm, stockage, tickets
from api.conversation import CRITIQUES, Conversation
from api.schemas import Action, Categorie, Decision, Label, Motif, Priorite, Source

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from historique import charger_historique, plus_semblable  # noqa: E402
from kb import article_le_plus_proche, categories_proches, charger_base  # noqa: E402
from kb import chercher as _chercher  # noqa: E402
from predict import charger_modele  # noqa: E402
from predict import predict as _predict  # noqa: E402

# Seuils choisis avec python src/courbe_seuil.py et le notebook (voir docs/semaine4.md).
SEUIL_ABSTENTION = 0.60
SEUIL_VOCABULAIRE = 0.50
# TP5.1 : similarité minimale de l'article le plus proche pour que la base tranche à la place du modèle.
# Mesuré sur le jeu d'évaluation (94 messages) et les 50 messages de développement : src/bilan_evaluation.py.
SEUIL_BASE = 0.25

# Étiquettes du modèle -> étiquettes du contrat. Toute autre étiquette est refusée au démarrage.
CORRESPONDANCE: dict[str, Categorie] = {
    "securite": "securite", "reseau": "reseau", "materiel": "materiel", "compte_acces": "compte_acces",
    "facturation": "facturation", "logiciel": "logiciel", "panne_service": "panne_service",
}
PRIORITES: dict[str, Priorite] = {"high": "high", "medium": "medium", "low": "low"}

# Un groupe de techniciens par catégorie (fiche cas1) ; l'incident incertain va au tri.
# Les noms sont en anglais : la page les montre à l'utilisateur (TP5).
GROUPES: dict[Label, str] = {
    "securite": "Security (SOC)",
    "reseau": "Network",
    "materiel": "Workstation",
    "compte_acces": "Identity and access",
    "facturation": "Billing",
    "logiciel": "Applications",
    "panne_service": "Operations (L2)",
    "INDETERMINE": "Triage (L1)",
}


class Prediction(TypedDict):
    """Ce que l'API renvoie pour un texte : le contrat de PredictResponse, vu par mypy."""

    label: Label
    score: float
    priorite: Priorite
    connus: float
    text: str
    source: Source


class Assistance(Prediction):
    """Ce que /assist renvoie : la prédiction, l'article et la décision (AssistResponse)."""

    decision: Decision
    motif: Motif
    raison: str
    groupe: str
    article: dict | None


class ConversationInconnue(KeyError):
    """Aucune conversation ne porte cet identifiant (l'API répond 404)."""


class SupportClassifier:
    """Enveloppe du modèle TP2 et de la base, avec l'interface attendue par l'API."""

    model_name: str = "tfidf-linearsvc (TP2, models/support.joblib)"

    def __init__(self) -> None:
        # Échoue immédiatement si le joblib ou la base manque : on ne démarre pas sans eux.
        modeles = charger_modele()
        # Échoue aussi si le modèle connaît des étiquettes que le contrat ignore.
        verifier_etiquettes("categorie", modeles["categorie"].classes_, set(CORRESPONDANCE))
        verifier_etiquettes("priorite", modeles["priorite"].classes_, set(PRIORITES))
        self.articles = len(charger_base()[0])

    def predict(self, text: str) -> Prediction:
        """Renvoie la catégorie du contrat (ou INDETERMINE), la confiance, la priorité et un aperçu."""
        r = _predict(text)
        label: Label = "INDETERMINE"
        source: Source = "aucune"
        if r["connus"] >= SEUIL_VOCABULAIRE:
            if r["score"] >= SEUIL_ABSTENTION:
                label, source = CORRESPONDANCE[r["label"]], "modele"
            else:  # le modèle hésite : la base de connaissances donne un second avis
                categorie, similarite = article_le_plus_proche(text)
                if similarite >= SEUIL_BASE:
                    label, source = CORRESPONDANCE[categorie], "base"
        return {"label": label, "score": r["score"], "priorite": PRIORITES[r["priorite"]], "connus": r["connus"],
                "text": text[:100], "source": source}

    def assist(self, text: str) -> Assistance:
        """Classe l'incident, cherche un article, puis applique les règles d'escalade."""
        prediction = self.predict(text)
        article = None if prediction["label"] == "INDETERMINE" else _chercher(text, prediction["label"])
        decision, motif, raison = decider_tp51(prediction, article)
        return {**prediction, "decision": decision, "motif": motif, "raison": raison,
                "groupe": GROUPES[prediction["label"]], "article": article}

    # --- Les outils de la conversation (TP5.1) ---

    def chercher(self, text: str, categorie: str, exclus: Iterable[str] = ()) -> dict | None:
        return _chercher(text, categorie, exclus)

    def creer_ticket_conversation(self, conv: Conversation) -> dict:
        """Le seul ticket de la conversation, pré-rempli : résumé, catégorie, étapes déjà essayées."""
        existant = tickets.pour_conversation(conv["id"])
        if existant is not None:
            return existant
        label: Label = conv["categorie"] or "INDETERMINE"
        dernier = conv["essais"][-1]["article_id"] if conv["essais"] else (conv["article"] or {}).get("id")
        return tickets.creer({
            "text": conversation.texte_complet(conv)[:2000], "label": label, "priorite": conv["priorite"],
            "groupe": GROUPES[label], "article_id": dernier, "raison": conversation.raison_du_ticket(conv),
            "conversation_id": conv["id"], "resume": conversation.resumer(conv), "essais": conv["essais"]})

    def ticket_semblable(self, conv: Conversation) -> dict | None:
        """Le ticket passé le plus proche : tickets résolus de l'agent, puis historique Tobi-Bueck."""
        resolus = [{"id": t["id"], "text": t["text"], "categorie": t["label"], "resolution": t.get("resolution"),
                    "source": "agent tickets"}
                   for t in tickets.lister() if t["statut"] in {"resolu", "ferme"} and t.get("conversation_id") != conv["id"]]
        texte = conversation.texte_complet(conv)
        return (plus_semblable(texte, resolus, conv["categorie"])
                or plus_semblable(texte, list(charger_historique()), conv["categorie"]))

    def discuter(self, conversation_id: str | None, action: Action, text: str | None = None,
                 categorie: Categorie | None = None, etapes_faites: Iterable[str] = ()) -> dict:
        """Un tour de conversation : charge l'état, applique la politique, sauvegarde, prépare la réponse."""
        if conversation_id is None:
            conv = conversation.nouvelle(f"CNV-{uuid.uuid4().hex[:8].upper()}")
        else:
            trouvee = stockage.lire("conversations", conversation_id)
            if trouvee is None:
                raise ConversationInconnue(conversation_id)
            conv = trouvee  # type: ignore[assignment]  # un dict relu du fichier, de la forme Conversation
        conv = conversation.avancer(conv, action, self, texte=text, categorie=categorie, etapes_faites=etapes_faites)
        stockage.ajouter("conversations", dict(conv))
        en_cours = conv["phase"] not in {"resolu", "ticket"}
        return {
            "conversation_id": conv["id"], "tour": len(conv["tours"]), "phase": conv["phase"], "code": conv["code"],
            "label": conv["label"], "score": conv["score"], "priorite": conv["priorite"],
            "categorie": conv["categorie"], "article": conv["article"],
            "categories": categories_proches(conversation.texte_complet(conv)) if conv["phase"] == "precision" else [],
            "choix": conversation.actions_possibles(conv), "tentatives": conv["tentatives"], "essais": conv["essais"],
            "ticket": tickets.lire(conv["ticket_id"]) if conv["ticket_id"] else None,
            "ticket_semblable": self.ticket_semblable(conv) if en_cours and conv["categorie"] else None,
            "reformulation": (llm.reformuler(conversation.texte_complet(conv), conv["article"])
                              if conv["phase"] == "solution" else None),
        }


def verifier_etiquettes(nom: str, classes: Iterable[object], connues: set[str]) -> None:
    """Refuse un modèle dont les classes ne sont pas toutes dans la correspondance du contrat."""
    inconnues = {str(c) for c in classes} - connues
    if inconnues:
        raise ValueError(f"étiquettes inconnues du modèle ({nom}) : {sorted(inconnues)}")


def decider(prediction: Prediction, article: dict | None) -> tuple[Decision, Motif, str]:
    """Les règles de la fiche cas1 (TP4), dans l'ordre : la première qui s'applique décide.
    Depuis le TP5.1, /assist utilise decider_tp51 ; celles-ci rejouent la page du TP5 (bilan des tickets).
    Dans le doute, on escalade : une escalade inutile coûte moins qu'une escalade manquée.
    Renvoie la décision, son motif (un code, que l'interface traduit pour l'utilisateur, TP5)
    et sa raison en clair (pour le technicien et le ticket)."""
    if prediction["label"] == "INDETERMINE":
        if prediction["connus"] < SEUIL_VOCABULAIRE:
            return "escalade", "mots_inconnus", (f"moins de la moitié des mots sont connus du modèle ({prediction['connus']:.0%}) : "
                                "langue ou vocabulaire inconnus, un technicien trie l'incident")
        return "escalade", "confiance_basse", (f"catégorie incertaine (confiance {prediction['score']:.2f} sous {SEUIL_ABSTENTION}) : "
                            "un technicien trie l'incident")
    if prediction["priorite"] == "high":
        return "escalade", "priorite_haute", "priorité haute : un technicien prend l'incident tout de suite"
    if article is None:
        return "escalade", "sans_article", "aucun article de la base ne correspond à cet incident"
    if article["escalade_si"].lower().startswith("always"):
        return "escalade", "article_escalade", f"l'article {article['id']} demande toujours un technicien"
    return "solution", "solution", f"article {article['id']} proposé : l'utilisateur essaie, puis dit si c'est résolu"


def decider_tp51(prediction: Prediction, article: dict | None) -> tuple[Decision, Motif, str]:
    """La décision de /assist depuis le TP5.1, alignée sur la conversation : un technicien seulement
    quand l'agent ne peut pas répondre seul (catégorie incertaine, aucun article) ou pour un cas
    critique. La priorité haute et les articles « always » ne suffisent plus : dans la conversation,
    l'agent propose d'abord les étapes. La priorité reste dans le ticket."""
    if prediction["label"] == "INDETERMINE":
        return decider(prediction, article)  # mots inconnus ou confiance basse : le tri N1, comme au TP4
    if prediction["label"] in CRITIQUES:
        return "escalade", "critique", "cas critique (sécurité ou panne générale) : un technicien prend l'incident"
    if article is None:
        return "escalade", "sans_article", "aucun article de la base ne correspond à cet incident"
    return "solution", "solution", f"article {article['id']} proposé : l'utilisateur essaie, puis dit si c'est résolu"


def load_model() -> SupportClassifier:
    """Construit le classifier (le cache de chargement est dans src/predict.py et src/kb.py)."""
    return SupportClassifier()
