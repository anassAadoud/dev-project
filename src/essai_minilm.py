#!/usr/bin/env python
"""TP5.2, phase 4 : l'hybride TF-IDF + all-MiniLM-L6-v2 contre le modèle actuel, sur la validation.

Le notebook minilm_vs_tfidf.ipynb (tickets Tobi-Bueck) : MiniLM seul perdait 5 points de F1, l'hybride
(TF-IDF et vecteurs MiniLM côte à côte) en gagnait 2. On teste donc l'hybride, pas MiniLM seul :

  actuel   mots + caractères -> LinearSVC calibré (le modèle de la phase 3 bis)
  H1       mots + caractères + vecteurs MiniLM (poids POIDS) -> LinearSVC calibré ; recherche d'articles inchangée
  H2       H1, et la recherche d'articles lit aussi les vecteurs MiniLM (index mots + caractères + MiniLM)

Mesuré sur 3 graines du jeu de démonstration : F1 macro, exactitude, faux, top-1 / top-3 des articles (méthode
« toute+ » de evaluer_articles.py), taux d'escalade de /assist (le taux de tickets du fichier), fausses
escalades, temps par message (/assist, encodeur chargé, sans cache).
Règle de décision (plan du TP5.2) : l'hybride n'est gardé que s'il gagne au moins 5 points de F1 macro ou de top-3.

Usage : python src/essai_minilm.py [--graines 3] [--poids 1.0]
Demande sentence-transformers et le modèle all-MiniLM-L6-v2 (téléchargé une fois dans le cache Hugging Face).
"""
import argparse
import logging
import statistics
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "src"))
SEUIL_GAIN = 0.05


def articles(clf, nom: str) -> tuple[float, float]:
    from evaluer_articles import lire, proposes

    lignes = lire(nom)
    un = trois = 0
    for ligne in lignes:
        ok = set(ligne["articles_ok"].split())
        ids = proposes(ligne["text"], clf.predict(ligne["text"]), "toute+")
        un += bool(ids) and ids[0] in ok
        trois += bool(ok & set(ids[:3]))
    return un / len(lignes), trois / len(lignes)


def temps_par_message(clf, textes: list[str]) -> float:
    """Millisecondes par message pour /assist, cache des vecteurs vidé : le cas d'un vrai message
    (le classement l'encode, la recherche d'articles réutilise le vecteur)."""
    from encodeur import Phrases

    clf.assist(textes[0])  # chauffe : chargement de l'encodeur
    Phrases._cache.clear()
    debut = time.perf_counter()
    for texte in textes:
        clf.assist(texte)
    return (time.perf_counter() - debut) * 1000 / len(textes)


def essayer(nom: str, graines: list[int], poids: float, jeu: str = "validation") -> list[dict]:
    """actuel : sans vecteurs de phrases ; H1 : dans le classement ; H2 : dans le classement et la recherche.
    Le code de production est utilisé (train.entrainer, kb.charger_index_recherche), avec ses interrupteurs."""
    import pandas as pd

    import evaluer
    import kb
    import make_demo
    import train
    from api.model import SupportClassifier

    poids_avant, mode_avant = train.POIDS_PHRASES, kb.mode_phrases
    train.POIDS_PHRASES = poids
    kb.mode_phrases = (lambda: "minilm") if nom == "H2" else (lambda: None)  # type: ignore[assignment]
    kb.charger_index_recherche.cache_clear()
    try:
        clf = SupportClassifier()
        lignes = evaluer.lire_jeu(jeu)
        textes = [ligne["text"] for ligne in lignes]
        resultats = []
        for graine in graines:
            df = pd.DataFrame(make_demo.generer(graine), columns=["text", "categorie", "priorite", "groupe"])
            entr, _ = train.decouper(df)
            modeles = train.entrainer(entr, phrases=nom != "actuel")
            with evaluer.modeles_en_memoire(modeles):
                m = evaluer.mesurer(clf, lignes)
                top1, top3 = articles(clf, jeu) if jeu == "validation" else (None, None)
                ms = temps_par_message(clf, textes)
            resultats.append({"f1": m["categorie"]["f1_macro"], "exactitude": m["categorie"]["exactitude"],
                              "faux": m["categorie"].get("faux"), "top1": top1, "top3": top3,
                              "escalade": m["escalade"]["taux"], "fausses": m["escalade"]["fausses_escalades"],
                              "ms": ms})
            print(f"  {nom} graine {graine} : {resultats[-1]}", flush=True)
        return resultats
    finally:
        train.POIDS_PHRASES = poids_avant
        kb.mode_phrases = mode_avant  # type: ignore[assignment]
        kb.charger_index_recherche.cache_clear()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--graines", type=int, default=3)
    parser.add_argument("--poids", type=float, default=1.0, help="poids des vecteurs MiniLM dans l'assemblage")
    parser.add_argument("--variantes", default="actuel,H1,H2")
    parser.add_argument("--jeu", default="validation", help="validation (décide) ; evaluation, jeu_or : veto")
    args = parser.parse_args()
    logging.disable(logging.INFO)
    import evaluer

    graines = evaluer.GRAINES[: args.graines]
    bilan = {}
    for nom in args.variantes.split(","):
        bilan[nom] = essayer(nom, graines, args.poids, args.jeu)
    print(f"\n== {args.jeu}, {len(graines)} graines, poids MiniLM {args.poids} (moyenne ± écart type)")
    cles = ["f1", "exactitude", "faux", "top1", "top3", "escalade", "fausses", "ms"]
    print(f"{'':8}" + "".join(f"{c:>18}" for c in cles))
    for nom, resultats in bilan.items():
        cellules = []
        for c in cles:
            valeurs = [r[c] for r in resultats if r[c] is not None]
            cellules.append(f"{statistics.mean(valeurs):.3f} ± {statistics.pstdev(valeurs):.3f}" if valeurs else "—")
        print(f"{nom:8}" + "".join(f"{c:>18}" for c in cellules))
    if "actuel" in bilan:
        def moyenne(nom: str, cle: str) -> float:
            valeurs = [r[cle] for r in bilan[nom] if r[cle] is not None]
            return statistics.mean(valeurs) if valeurs else 0.0

        for nom in [n for n in bilan if n != "actuel"]:
            gain_f1 = moyenne(nom, "f1") - moyenne("actuel", "f1")
            gain_top3 = moyenne(nom, "top3") - moyenne("actuel", "top3")
            garde = gain_f1 >= SEUIL_GAIN or gain_top3 >= SEUIL_GAIN
            print(f"{nom} : F1 macro {gain_f1:+.3f}, top-3 {gain_top3:+.3f} -> {'gardé' if garde else 'non gardé'} "
                  f"(seuil {SEUIL_GAIN:+.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
