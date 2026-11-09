#!/usr/bin/env python
"""Qualité des réponses (TP5.2, phase 3 bis) : le bon article est-il proposé ?

Pour chaque incident d'un jeu étiqueté (colonne articles_ok : les articles qui règlent l'incident),
l'agent classe le message comme l'API (SupportClassifier.predict), puis cherche ses articles :
  categorie  la méthode du TP5.1 : les articles de la catégorie prédite seulement, index de mots
  toute      la méthode du TP5.2 : toute la base, bonus pour la catégorie prédite (kb.proposer)
  toute+     comme « toute », et des articles aussi quand le modèle hésite (catégorie inconnue)
  diagnostic comme « toute+ », après une réponse à la question de diagnostic de la catégorie prédite :
             l'utilisateur simulé choisit la réponse qui cite un des bons articles (sinon une réponse sans effet)

top-1 : le premier article proposé est dans articles_ok ; top-3 : un des trois l'est.
Un incident sans article proposé compte comme manqué. Le hors sujet n'a pas d'articles_ok : il est à part.

Usage, depuis la racine du dépôt, modèle entraîné :
  python src/evaluer_articles.py validation
  python src/evaluer_articles.py validation --methode categorie
"""
import argparse
import csv
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "src"))
JEUX = {"validation": RACINE / "data" / "jeu_validation.csv", "independant": RACINE / "data" / "jeu_independant.csv"}
METHODES = ["categorie", "toute", "toute+", "diagnostic"]


def lire(nom: str) -> list[dict[str, str]]:
    with JEUX[nom].open(encoding="utf-8", newline="") as f:
        return [ligne for ligne in csv.DictReader(f) if (ligne.get("articles_ok") or "").strip()]


def articles_categorie(texte: str, categorie: str, nombre: int = 3) -> list[str]:
    """La recherche du TP5.1 : la catégorie prédite seulement, index de mots, seuil de similarité."""
    import kb

    articles, similarites = kb._similarites(texte)
    candidats = [i for i, a in enumerate(articles) if a["categorie"] == categorie and similarites[i] >= kb.SEUIL_SIMILARITE]
    candidats.sort(key=lambda i: -similarites[i])
    return [articles[i]["id"] for i in candidats[:nombre]]


def reponse_simulee(questions: list[dict], ok: set[str]) -> list[str]:
    """Les articles préférés après la première question qui a une réponse citant un bon article."""
    for question in questions:
        for option in question["options"]:
            articles = (option.get("effet") or {}).get("articles") or []
            if ok & set(articles):
                return list(articles)
    return []


def proposes(texte: str, prediction: Mapping[str, Any], methode: str, preferes: list[str] | None = None) -> list[str]:
    import kb
    from predict import partie_principale

    principal = partie_principale(texte)
    label = prediction["label"]
    if methode == "categorie":
        return [] if label == "INDETERMINE" else articles_categorie(principal, label)
    if label == "INDETERMINE" and (methode == "toute" or prediction.get("source") == "hors_sujet"):
        return []
    return [a["id"] for a in kb.proposer(principal, None if label == "INDETERMINE" else label, preferes=preferes or [])]


def mesurer(nom: str, methode: str) -> dict:
    from api.model import SupportClassifier

    clf = SupportClassifier()
    lignes = lire(nom)
    top1 = top3 = aucun = 0
    par_categorie: dict[str, list[int]] = {}
    for ligne in lignes:
        ok = set(ligne["articles_ok"].split())
        prediction = clf.predict(ligne["text"])
        preferes = (reponse_simulee(clf.questions(prediction["label"]), ok)
                    if methode == "diagnostic" and prediction["label"] != "INDETERMINE" else [])
        ids = proposes(ligne["text"], prediction, "toute+" if methode == "diagnostic" else methode, preferes)
        un, trois = bool(ids) and ids[0] in ok, bool(ok & set(ids[:3]))
        top1, top3, aucun = top1 + un, top3 + trois, aucun + (not ids)
        par_categorie.setdefault(ligne["attendu"], [0, 0, 0])
        compte = par_categorie[ligne["attendu"]]
        compte[0], compte[1], compte[2] = compte[0] + un, compte[1] + trois, compte[2] + 1
    n = len(lignes)
    return {"jeu": nom, "methode": methode, "incidents": n, "top1": round(top1 / n, 3), "top3": round(top3 / n, 3),
            "sans_article": round(aucun / n, 3), "par_categorie": par_categorie}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("jeu", choices=sorted(JEUX))
    parser.add_argument("--methode", choices=METHODES, default="toute")
    args = parser.parse_args()
    r = mesurer(args.jeu, args.methode)
    print(f"{r['jeu']} ({r['incidents']} incidents), méthode {r['methode']} : top-1 {r['top1']:.1%}, "
          f"top-3 {r['top3']:.1%}, sans article {r['sans_article']:.1%}")
    for categorie, (un, trois, n) in sorted(r["par_categorie"].items()):
        print(f"  {categorie:<14} top-1 {un:>2}/{n}  top-3 {trois:>2}/{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
