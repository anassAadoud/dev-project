#!/usr/bin/env python
"""Bilan sur le jeu d'évaluation (TP5.1) : 94 messages jamais utilisés pour écrire la base ni le jeu
de démonstration (12 par catégorie, 10 hors sujet).

Pour chaque message, ce que l'API classe (/predict) :
  - « juste » : la bonne catégorie, ou INDETERMINE pour un message hors sujet ;
  - « faux » : une autre catégorie (l'erreur qui coûte : une procédure inadaptée) ;
  - « hésite » : INDETERMINE pour un vrai incident (la conversation pose alors une question).

Usage, depuis la racine du dépôt, modèle entraîné :
  python src/bilan_evaluation.py                 # le jeu d'évaluation
  python src/bilan_evaluation.py results.csv     # en plus : la part d'INDETERMINE sur un fichier de tickets
"""
import csv
import logging
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
JEU = RACINE / "data" / "jeu_evaluation.csv"
CATEGORIES = ["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]


def lire_jeu() -> list[dict[str, str]]:
    with JEU.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def issue(label: str, attendu: str) -> str:
    if attendu == "hors_sujet":
        return "juste" if label == "INDETERMINE" else "faux"
    if label == "INDETERMINE":
        return "hésite"
    return "juste" if label == attendu else "faux"


def evaluer(clf, lignes: list[dict[str, str]]) -> dict[str, Counter]:
    """Les issues par catégorie attendue (et « total »)."""
    bilan: dict[str, Counter] = {c: Counter() for c in [*CATEGORIES, "hors_sujet", "total"]}
    for ligne in lignes:
        resultat = issue(clf.predict(ligne["text"])["label"], ligne["attendu"])
        bilan[ligne["attendu"]][resultat] += 1
        bilan["total"][resultat] += 1
    return bilan


def main() -> int:
    sys.path.insert(0, str(RACINE))
    from api.model import load_model

    logging.disable(logging.INFO)
    clf = load_model()
    lignes = lire_jeu()
    bilan = evaluer(clf, lignes)
    print(f"{'catégorie':<14} {'juste':>6} {'faux':>5} {'hésite':>7}")
    for nom, compte in bilan.items():
        print(f"{nom:<14} {compte['juste']:>6} {compte['faux']:>5} {compte['hésite']:>7}")
    total = bilan["total"]
    print(f"\nJeu d'évaluation : {total['juste']} justes sur {len(lignes)} ({total['juste'] / len(lignes):.0%}), "
          f"{total['faux']} faux, {total['hésite']} hésitations")

    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8", newline="") as f:
            textes = [ligne["text"] for ligne in csv.DictReader(f) if (ligne.get("text") or "").strip()]
        labels = Counter(clf.predict(t)["label"] for t in textes)
        print(f"{sys.argv[1]} : INDETERMINE {labels['INDETERMINE']} sur {len(textes)} "
              f"({labels['INDETERMINE'] / len(textes):.0%}) ; "
              + ", ".join(f"{c} {labels[c]}" for c in CATEGORIES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
