#!/usr/bin/env python
"""Évalue le modèle sauvegardé et affiche la matrice de confusion des catégories.

Usage :
  python src/evaluate.py          # sur le jeu de démonstration
  python src/evaluate.py --reel   # sur le jeu Tobi-Bueck
"""
import argparse
import sys
from pathlib import Path

import joblib
from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))   # pour lancer depuis la racine
from train import CATEGORIES, MODELE, charger, decouper  # mêmes constantes, même découpage

# Abréviations pour que la matrice 7 x 7 tienne dans un terminal
COURT = {"securite": "secu", "reseau": "reseau", "materiel": "mater", "compte_acces": "compte",
         "facturation": "factu", "logiciel": "logic", "panne_service": "panne"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reel", action="store_true")
    args = parser.parse_args()

    if not MODELE.exists():
        raise SystemExit("Modèle absent : lancez d'abord python src/train.py")
    pipeline = joblib.load(MODELE)["categorie"]

    df, source = charger(args.reel)
    _, test = decouper(df)  # même graine, mêmes proportions que l'entraînement
    y_pred = pipeline.predict(test["text"])

    print(f"Évaluation sur {len(test)} incidents ({source})\n")
    print(classification_report(test["categorie"], y_pred, digits=3, zero_division=0))
    mc = confusion_matrix(test["categorie"], y_pred, labels=CATEGORIES)
    print("Matrice de confusion (lignes = vérité, colonnes = prédiction)")
    print(f"{'':>8}" + "".join(f"{COURT[c]:>8}" for c in CATEGORIES))
    for nom, ligne in zip(CATEGORIES, mc, strict=True):
        print(f"{COURT[nom]:>8}" + "".join(f"{v:>8}" for v in ligne))

    erreurs = [(t, v, p) for t, v, p in zip(test["text"], test["categorie"], y_pred, strict=True) if v != p]
    print(f"\n{len(erreurs)} erreurs sur {len(test)}. Trois exemples :")
    for texte, vrai, predit in erreurs[:3]:
        print(f"  vérité={vrai:13s} prédit={predit:13s} | {texte[:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
