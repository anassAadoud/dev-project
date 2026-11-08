#!/usr/bin/env python
"""Prédiction unitaire : la catégorie IT d'un incident, sa confiance, sa priorité (TP2, typé au TP4).

Usage :
  python src/predict.py "My VPN keeps disconnecting every 10 minutes"
  >>> from predict import predict ; predict("texte")
"""
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

import joblib
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

RACINE = Path(__file__).resolve().parents[1]
MODELE = RACINE / "models" / "support.joblib"


class Resultat(TypedDict):
    """Ce que renvoie predict() : l'étiquette du modèle, sa confiance, la priorité, et la part
    des mots du texte que le modèle connaît (le garde-fou de vocabulaire du TP4)."""

    label: str
    score: float
    priorite: str
    connus: float


@lru_cache(maxsize=1)
def charger_modele() -> Any:
    """Chargé une seule fois par processus, pas à chaque appel."""
    if not MODELE.exists():
        # Chemin complet, pas relatif au dépôt : le modèle peut se trouver ailleurs (TP4, test d'intégration).
        raise FileNotFoundError(f"modèle introuvable : {MODELE}. Lancez python src/train.py")
    return joblib.load(MODELE)


def part_connue(texte: str, vectoriseur: Any) -> float:
    """Part des mots du texte (unigrammes) présents dans le vocabulaire du modèle (notebook, section 15.1).

    TP5.1 : les mots vides anglais (the, is, on, our…) ne comptent plus. Ils sont connus de tout
    modèle et ne disent rien de l'incident : « Our coffee machine leaks water on the floor » passait
    le garde-fou avec 50 % de mots « connus », dont aucun ne parlait d'informatique."""
    mots = [t for t in vectoriseur.build_analyzer()(texte) if " " not in t and t not in ENGLISH_STOP_WORDS]
    return sum(t in vectoriseur.vocabulary_ for t in mots) / len(mots) if mots else 0.0


def predict(texte: str) -> Resultat:
    """Renvoie {'label': catégorie, 'score': confiance, 'priorite': ..., 'connus': part de mots connus}."""
    if not isinstance(texte, str) or not texte.strip():
        raise ValueError("texte vide")
    modeles = charger_modele()
    categorie = modeles["categorie"]
    probas = categorie.predict_proba([texte])[0]
    return {
        "label": str(categorie.classes_[probas.argmax()]),
        "score": round(float(probas.max()), 4),
        "priorite": str(modeles["priorite"].predict([texte])[0]),
        "connus": round(part_connue(texte, categorie.named_steps["tfidf"]), 4),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    resultat = predict(" ".join(sys.argv[1:]))
    print(f"{resultat['label']} (confiance {resultat['score']:.0%}, priorité {resultat['priorite']}, "
          f"mots connus {resultat['connus']:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
