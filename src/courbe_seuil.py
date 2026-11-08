#!/usr/bin/env python
"""Courbe du seuil d'abstention, mesurée sur le jeu de test du TP2 (TP4, étape C).

Le modèle ne répond que si sa confiance atteint le seuil ; sinon l'incident part vers
le tri N1. Pour chaque seuil, on lit la part des incidents auxquels il répond, et son
exactitude sur ces seuls incidents. La dernière colonne rappelle le garde-fou de
vocabulaire : les incidents dont moins de la moitié des mots sont connus du modèle.

Usage, depuis la racine du dépôt :
  python src/courbe_seuil.py          # jeu de démonstration
  python src/courbe_seuil.py --reel   # jeu Tobi-Bueck
Le modèle doit avoir été entraîné sur les mêmes données que la courbe.
"""
import argparse
import json
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predict import part_connue  # noqa: E402  (la règle du garde-fou, celle de l'API)
from train import METRIQUES, MODELE, charger, decouper  # noqa: E402  (même découpage que train.py)

SEUILS = [round(0.30 + 0.05 * i, 2) for i in range(14)]  # de 0,30 à 0,95 : 7 classes, des confiances plus basses
SEUIL_VOCABULAIRE = 0.5


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reel", action="store_true", help="courbe sur le jeu Tobi-Bueck")
    args = parser.parse_args()

    if not MODELE.exists():
        raise SystemExit("Modèle absent : lancez d'abord python src/train.py")
    df, source = charger(args.reel)
    if METRIQUES.exists():
        entraine_sur = str(json.loads(METRIQUES.read_text(encoding="utf-8")).get("source", "?"))
        if entraine_sur != source:
            print(f"ATTENTION : modèle entraîné sur « {entraine_sur} », courbe calculée sur « {source} ».")
            print("Réentraînez sur les mêmes données : sinon la courbe ne mesure pas votre modèle.\n")

    # Même découpage que l'entraînement : seul le jeu de test, jamais vu par le modèle, est mesuré
    _, test = decouper(df)
    pipeline = joblib.load(MODELE)["categorie"]
    probas = pipeline.predict_proba(test["text"])
    confiance = probas.max(axis=1)
    justes = pipeline.classes_[probas.argmax(axis=1)] == test["categorie"].to_numpy()
    vectoriseur = pipeline.named_steps["tfidf"]
    inconnus = sum(part_connue(t, vectoriseur) < SEUIL_VOCABULAIRE for t in test["text"])
    n = len(test)

    print(f"Jeu de test : {n} incidents ({source}) ; garde-fou de vocabulaire : {inconnus} sous {SEUIL_VOCABULAIRE:.0%}\n")
    print(f"{'seuil':>6} {'répond à':>9} {'part':>6} {'exactitude':>11} {'erreurs':>8} {'vers un humain':>15}")
    for seuil in SEUILS:
        repond = confiance >= seuil
        k = int(repond.sum())
        exactitude = f"{justes[repond].mean():.3f}" if k else "-"
        erreurs = int((~justes[repond]).sum())
        print(f"{seuil:>6.2f} {k:>9d} {k / n:>6.0%} {exactitude:>11} {erreurs:>8d} {n - k:>15d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
