#!/usr/bin/env python
"""Prédiction unitaire : la catégorie IT d'un incident, sa confiance et sa priorité.

Usage :
  python src/predict.py "My VPN keeps disconnecting every 10 minutes"
  >>> from predict import predict ; predict("texte")
"""
import sys
from functools import lru_cache
from pathlib import Path

import joblib

RACINE = Path(__file__).resolve().parents[1]
MODELE = RACINE / "models" / "support.joblib"


@lru_cache(maxsize=1)
def charger_modele():
    """Chargé une seule fois par processus, pas à chaque appel."""
    if not MODELE.exists():
        raise FileNotFoundError(f"{MODELE.relative_to(RACINE).as_posix()} absent : lancez python src/train.py")
    return joblib.load(MODELE)


def predict(texte):
    """Renvoie {'label': catégorie, 'score': confiance, 'priorite': 'high'|'medium'|'low'}."""
    if not isinstance(texte, str) or not texte.strip():
        raise ValueError("texte vide")
    modeles = charger_modele()
    probas = modeles["categorie"].predict_proba([texte])[0]
    categorie = str(modeles["categorie"].classes_[probas.argmax()])
    priorite = str(modeles["priorite"].predict([texte])[0])
    return {"label": categorie, "score": round(float(probas.max()), 4), "priorite": priorite}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    resultat = predict(" ".join(sys.argv[1:]))
    print(f"{resultat['label']} (confiance {resultat['score']:.0%}, priorité {resultat['priorite']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
