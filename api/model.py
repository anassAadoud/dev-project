"""Raccord entre l'API, le modèle du TP2 et la base de connaissances.

L'API n'entraîne rien et ne connaît pas scikit-learn : elle appelle predict() du TP2,
qui charge models/support.joblib une seule fois, et chercher() de src/kb.py.
Les règles d'escalade de la fiche cas1 vivent ici : elles sont lisibles et testées.

TP4 : l'API s'abstient (INDETERMINE) au lieu de deviner, dans deux cas : la confiance est
sous SEUIL_ABSTENTION, ou moins de SEUIL_VOCABULAIRE des mots sont connus du modèle.
Les étiquettes du modèle passent par des correspondances explicites, vérifiées au démarrage.
"""
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import TypedDict

from api.schemas import Categorie, Decision, Label, Priorite

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from kb import charger_base, chercher  # noqa: E402
from predict import charger_modele  # noqa: E402
from predict import predict as _predict  # noqa: E402

# Seuils choisis avec python src/courbe_seuil.py et le notebook (voir docs/semaine4.md).
SEUIL_ABSTENTION = 0.60
SEUIL_VOCABULAIRE = 0.50

# Étiquettes du modèle -> étiquettes du contrat. Toute autre étiquette est refusée au démarrage.
CORRESPONDANCE: dict[str, Categorie] = {
    "securite": "securite", "reseau": "reseau", "materiel": "materiel", "compte_acces": "compte_acces",
    "facturation": "facturation", "logiciel": "logiciel", "panne_service": "panne_service",
}
PRIORITES: dict[str, Priorite] = {"high": "high", "medium": "medium", "low": "low"}

# Un groupe de techniciens par catégorie (fiche cas1) ; l'incident incertain va au tri.
GROUPES: dict[Label, str] = {
    "securite": "Sécurité (SOC)",
    "reseau": "Réseau",
    "materiel": "Poste de travail",
    "compte_acces": "Identités et accès",
    "facturation": "Facturation",
    "logiciel": "Applications",
    "panne_service": "Exploitation (N2)",
    "INDETERMINE": "Tri N1",
}


class Prediction(TypedDict):
    """Ce que l'API renvoie pour un texte : le contrat de PredictResponse, vu par mypy."""

    label: Label
    score: float
    priorite: Priorite
    connus: float
    text: str


class Assistance(Prediction):
    """Ce que /assist renvoie : la prédiction, l'article et la décision (AssistResponse)."""

    decision: Decision
    raison: str
    groupe: str
    article: dict | None


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
        sur = r["score"] >= SEUIL_ABSTENTION and r["connus"] >= SEUIL_VOCABULAIRE
        label: Label = CORRESPONDANCE[r["label"]] if sur else "INDETERMINE"
        return {"label": label, "score": r["score"], "priorite": PRIORITES[r["priorite"]], "connus": r["connus"],
                "text": text[:100]}

    def assist(self, text: str) -> Assistance:
        """Classe l'incident, cherche un article, puis applique les règles d'escalade."""
        prediction = self.predict(text)
        article = None if prediction["label"] == "INDETERMINE" else chercher(text, prediction["label"])
        decision, raison = decider(prediction, article)
        return {**prediction, "decision": decision, "raison": raison,
                "groupe": GROUPES[prediction["label"]], "article": article}


def verifier_etiquettes(nom: str, classes: Iterable[object], connues: set[str]) -> None:
    """Refuse un modèle dont les classes ne sont pas toutes dans la correspondance du contrat."""
    inconnues = {str(c) for c in classes} - connues
    if inconnues:
        raise ValueError(f"étiquettes inconnues du modèle ({nom}) : {sorted(inconnues)}")


def decider(prediction: Prediction, article: dict | None) -> tuple[Decision, str]:
    """Les règles de la fiche cas1, dans l'ordre : la première qui s'applique décide.
    Dans le doute, on escalade : une escalade inutile coûte moins qu'une escalade manquée."""
    if prediction["label"] == "INDETERMINE":
        if prediction["connus"] < SEUIL_VOCABULAIRE:
            return "escalade", (f"moins de la moitié des mots sont connus du modèle ({prediction['connus']:.0%}) : "
                                "langue ou vocabulaire inconnus, un technicien trie l'incident")
        return "escalade", (f"catégorie incertaine (confiance {prediction['score']:.2f} sous {SEUIL_ABSTENTION}) : "
                            "un technicien trie l'incident")
    if prediction["priorite"] == "high":
        return "escalade", "priorité haute : un technicien prend l'incident tout de suite"
    if article is None:
        return "escalade", "aucun article de la base ne correspond à cet incident"
    if article["escalade_si"].lower().startswith("always"):
        return "escalade", f"l'article {article['id']} demande toujours un technicien"
    return "solution", f"article {article['id']} proposé : l'utilisateur essaie, puis dit si c'est résolu"


def load_model() -> SupportClassifier:
    """Construit le classifier (le cache de chargement est dans src/predict.py et src/kb.py)."""
    return SupportClassifier()
