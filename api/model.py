"""Raccord entre l'API, le modèle du TP2 et la base de connaissances.

L'API n'entraîne rien et ne connaît pas scikit-learn : elle appelle predict() du TP2,
qui charge models/support.joblib une seule fois, et chercher() de src/kb.py.
Les règles d'escalade de la fiche cas1 vivent ici : elles sont lisibles et testées.
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
from kb import charger_base, chercher  # noqa: E402
from predict import charger_modele  # noqa: E402
from predict import predict as _predict  # noqa: E402

# Un groupe de techniciens par catégorie (fiche cas1).
GROUPES = {
    "securite": "Sécurité (SOC)",
    "reseau": "Réseau",
    "materiel": "Poste de travail",
    "compte_acces": "Identités et accès",
    "facturation": "Facturation",
    "logiciel": "Applications",
    "panne_service": "Exploitation (N2)",
}


class SupportClassifier:
    """Enveloppe du modèle TP2 et de la base, avec l'interface attendue par l'API."""

    model_name: str = "tfidf-linearsvc (TP2, models/support.joblib)"

    def __init__(self) -> None:
        # Échoue immédiatement si le joblib ou la base manque : on ne démarre pas sans eux.
        charger_modele()
        self.articles = len(charger_base()[0])

    def predict(self, text: str) -> dict:
        r = _predict(text)
        return {"label": r["label"], "score": r["score"], "priorite": r["priorite"], "text": text[:100]}

    def assist(self, text: str) -> dict:
        """Classe l'incident, cherche un article, puis applique les règles d'escalade."""
        prediction = self.predict(text)
        article = chercher(text, prediction["label"])
        decision, raison = decider(prediction, article)
        return {**prediction, "decision": decision, "raison": raison,
                "groupe": GROUPES[prediction["label"]], "article": article}


def decider(prediction: dict, article: dict | None) -> tuple[str, str]:
    """Les règles de la fiche cas1, dans l'ordre : la première qui s'applique décide.
    Dans le doute, on escalade : une escalade inutile coûte moins qu'une escalade manquée."""
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
