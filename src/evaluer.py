#!/usr/bin/env python
"""Évaluation complète de l'agent (TP5.2) : catégorie, priorité, escalade, sur des jeux étiquetés.

Les jeux et leur rôle (voir docs/semaine5.2.md) :
  validation   data/jeu_validation.csv   le SEUL jeu sur lequel on règle les seuils et choisit les options
  independant  data/jeu_independant.csv lu pour la mesure de départ et la mesure finale, jamais pour décider
  tobi         partie test (20 %) de Tobi-Bueck, réelle, jamais vue à l'entraînement (réseau ou copie locale)
  evaluation, jeu_or, conversations_30   jeux du TP4 et du TP5.1, déjà vus : tests de régression seulement

Ce qui est mesuré, sur les messages informatiques (hors sujet à part) :
  catégorie   exactitude, F1 macro et pondéré, précision / rappel / F1 par catégorie, matrice de confusion,
              taux d'abstention, couverture et exactitude quand l'agent répond, erreur de calibration (ECE)
  hors sujet  part des messages hors sujet que l'agent refuse de classer
  priorité    exactitude, matrice de confusion, messages calmes marqués high
  escalade    taux d'escalade de /assist, fausses escalades (incident non critique qui part au technicien),
              faux cas critiques (escalade « critique » d'un incident qui ne l'est pas), cas critiques manqués

Usage, depuis la racine du dépôt, modèle entraîné :
  python src/evaluer.py validation
  python src/evaluer.py validation --graines 5      # en plus : 5 jeux de démonstration, 5 modèles en mémoire
  python src/evaluer.py independant --json models/evaluation_independant.json
"""
import argparse
import csv
import json
import logging
import statistics
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
CATEGORIES = ["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]
CRITIQUES = {"securite", "panne_service"}
JEUX = {
    "validation": RACINE / "data" / "jeu_validation.csv",
    "independant": RACINE / "data" / "jeu_independant.csv",
    "evaluation": RACINE / "data" / "jeu_evaluation.csv",
    "jeu_or": RACINE / "data" / "jeu_or.csv",
    "conversations_30": RACINE / "data" / "conversations_30.csv",
}
GRAINES = [1, 2, 3, 4, 5]


def lire_jeu(nom: str) -> list[dict[str, str]]:
    """Les lignes d'un jeu : text, attendu (une catégorie ou hors_sujet), priorite (éventuellement vide)."""
    if nom == "tobi":
        sys.path.insert(0, str(RACINE / "src"))
        import train

        df, _ = train.charger(reel=True)
        _, test = train.decouper(df)
        return [{"text": t, "attendu": c, "priorite": p} for t, c, p in zip(test["text"], test["categorie"],
                                                                          test["priorite"], strict=True)]
    with JEUX[nom].open(encoding="utf-8", newline="") as f:
        lignes = [ligne for ligne in csv.DictReader(f) if (ligne.get("text") or "").strip()]
    return [{"text": ligne["text"], "attendu": ligne["attendu"], "priorite": ligne.get("priorite") or ""}
            for ligne in lignes]


def ece(confiances: list[float], justes: list[bool], paniers: int = 10) -> float:
    """Erreur de calibration attendue : l'écart moyen entre la confiance annoncée et l'exactitude réelle."""
    total = 0.0
    for b in range(paniers):
        dedans = [(c, j) for c, j in zip(confiances, justes, strict=True) if b / paniers < c <= (b + 1) / paniers]
        if dedans:
            total += len(dedans) / len(confiances) * abs(sum(j for _, j in dedans) / len(dedans)
                                                         - sum(c for c, _ in dedans) / len(dedans))
    return round(total, 4)


def f1_par_classe(vrais: list[str], predits: list[str]) -> dict[str, dict[str, float]]:
    """Précision, rappel, F1 et support pour chaque catégorie (une abstention compte comme un rappel manqué)."""
    sortie = {}
    for c in CATEGORIES:
        vp = sum(1 for v, p in zip(vrais, predits, strict=True) if v == c and p == c)
        np_ = sum(1 for p in predits if p == c)
        nv = sum(1 for v in vrais if v == c)
        precision = vp / np_ if np_ else 0.0
        rappel = vp / nv if nv else 0.0
        f1 = 2 * precision * rappel / (precision + rappel) if precision + rappel else 0.0
        sortie[c] = {"precision": round(precision, 4), "rappel": round(rappel, 4), "f1": round(f1, 4), "support": nv}
    return sortie


def mesurer(clf, lignes: list[dict[str, str]]) -> dict:
    """Toutes les mesures d'un classifier de l'API (SupportClassifier) sur un jeu étiqueté."""
    import predict as module_predict

    it = [ligne for ligne in lignes if ligne["attendu"] in CATEGORIES]
    hors = [ligne for ligne in lignes if ligne["attendu"] not in CATEGORIES]
    aides = {ligne["text"]: clf.assist(ligne["text"]) for ligne in lignes}
    vrais = [ligne["attendu"] for ligne in it]
    predits = [aides[ligne["text"]]["label"] for ligne in it]
    par_classe = f1_par_classe(vrais, predits)
    supports = sum(v["support"] for v in par_classe.values())
    repond = [(v, p) for v, p in zip(vrais, predits, strict=True) if p != "INDETERMINE"]
    bruts = [module_predict.predict(ligne["text"]) for ligne in it]

    avec_priorite = [ligne for ligne in it if ligne["priorite"]]
    p_vrais = [ligne["priorite"] for ligne in avec_priorite]
    p_predits = [aides[ligne["text"]]["priorite"] for ligne in avec_priorite]
    decisions = {ligne["text"]: (aides[ligne["text"]]["decision"], aides[ligne["text"]]["motif"]) for ligne in lignes}
    non_critiques = [ligne for ligne in it if ligne["attendu"] not in CRITIQUES]
    critiques = [ligne for ligne in it if ligne["attendu"] in CRITIQUES]

    def part(n: int, total: int) -> float | None:
        return round(n / total, 4) if total else None

    return {
        "messages": len(lignes), "informatiques": len(it), "hors_sujet": len(hors),
        "categorie": {
            "exactitude": part(sum(v == p for v, p in zip(vrais, predits, strict=True)), len(it)),
            "f1_macro": round(sum(v["f1"] for v in par_classe.values()) / len(CATEGORIES), 4),
            "f1_pondere": round(sum(v["f1"] * v["support"] for v in par_classe.values()) / supports, 4) if supports else None,
            "abstention": part(sum(p == "INDETERMINE" for p in predits), len(it)),
            "couverture": part(len(repond), len(it)),
            "exactitude_quand_repond": part(sum(v == p for v, p in repond), len(repond)),
            "faux": sum(1 for v, p in repond if v != p),
            "ece_modele": ece([b["score"] for b in bruts], [b["label"] == v for b, v in zip(bruts, vrais, strict=True)]),
            "par_classe": par_classe,
            "confusion": {v: dict(Counter(p for vv, p in zip(vrais, predits, strict=True) if vv == v)) for v in CATEGORIES},
        },
        "hors_sujet_refuse": part(sum(aides[ligne["text"]]["label"] == "INDETERMINE" for ligne in hors), len(hors)),
        "priorite": {
            "messages": len(avec_priorite),
            "exactitude": part(sum(v == p for v, p in zip(p_vrais, p_predits, strict=True)), len(avec_priorite)),
            "calmes_marques_high": sum(1 for v, p in zip(p_vrais, p_predits, strict=True) if v == "low" and p == "high"),
            "confusion": {v: dict(Counter(p for vv, p in zip(p_vrais, p_predits, strict=True) if vv == v))
                          for v in ["high", "medium", "low"]},
        },
        "escalade": {
            "taux": part(sum(d == "escalade" for d, _ in decisions.values()), len(lignes)),
            "fausses_escalades": part(sum(decisions[ligne["text"]][0] == "escalade" for ligne in non_critiques),
                                      len(non_critiques)),
            "faux_critiques": sum(1 for ligne in lignes
                                  if decisions[ligne["text"]][1] == "critique" and ligne["attendu"] not in CRITIQUES),
            "critiques_manques": sum(1 for ligne in critiques if decisions[ligne["text"]][0] != "escalade"),
        },
    }


@contextmanager
def modeles_en_memoire(modeles: dict):
    """Fait servir à l'API des modèles construits en mémoire (évaluation sur plusieurs graines)."""
    import predict as module_predict

    original = module_predict.charger_modele
    module_predict.charger_modele = lambda: modeles  # type: ignore[assignment]
    try:
        yield
    finally:
        module_predict.charger_modele = original


def sur_plusieurs_graines(clf, lignes: list[dict[str, str]], graines: list[int] = GRAINES) -> list[dict]:
    """Le même code, entraîné sur des jeux de démonstration tirés avec d'autres graines."""
    import pandas as pd

    import make_demo
    import train

    resultats = []
    for graine in graines:
        df = pd.DataFrame(make_demo.generer(graine), columns=["text", "categorie", "priorite", "groupe"])
        entr, _ = train.decouper(df)
        modeles = train.entrainer(entr) if hasattr(train, "entrainer") else {
            "categorie": train.construire_pipeline().fit(entr["text"], entr["categorie"]),
            "priorite": train.construire_pipeline_priorite().fit(entr["text"], entr["priorite"])}
        with modeles_en_memoire(modeles):
            resultats.append(mesurer(clf, lignes))
    return resultats


def moyenne_ecart(valeurs: list[float]) -> str:
    return f"{statistics.mean(valeurs):.3f} ± {statistics.pstdev(valeurs):.3f}"


def afficher(m: dict, nom: str) -> None:
    c, p, e = m["categorie"], m["priorite"], m["escalade"]
    print(f"== {nom} : {m['messages']} messages ({m['informatiques']} informatiques, {m['hors_sujet']} hors sujet)")
    print(f"catégorie : exactitude {c['exactitude']:.1%}, F1 macro {c['f1_macro']:.3f}, F1 pondéré {c['f1_pondere']:.3f} ; "
          f"abstention {c['abstention']:.1%}, exactitude quand il répond {c['exactitude_quand_repond']:.1%} "
          f"({c['faux']} faux) ; ECE du modèle {c['ece_modele']:.3f}")
    print(f"{'':>15}{'précision':>10}{'rappel':>8}{'F1':>7}{'n':>5}")
    for cat, v in c["par_classe"].items():
        print(f"{cat:>15}{v['precision']:>10.2f}{v['rappel']:>8.2f}{v['f1']:>7.2f}{v['support']:>5}")
    colonnes = [*CATEGORIES, "INDETERMINE"]
    print("confusion (lignes : attendu ; colonnes : " + ", ".join(x[:6] for x in colonnes) + ")")
    for v in CATEGORIES:
        print(f"{v:>15} " + " ".join(f"{c['confusion'][v].get(k, 0):>6}" for k in colonnes))
    if m["hors_sujet"]:
        print(f"hors sujet refusé : {m['hors_sujet_refuse']:.0%}")
    if p["messages"]:
        print(f"priorité : exactitude {p['exactitude']:.1%} sur {p['messages']} ; calmes marqués high {p['calmes_marques_high']} ; "
              f"confusion {p['confusion']}")
    print(f"escalade : {e['taux']:.1%} des messages ; fausses escalades {e['fausses_escalades']:.1%} des incidents non "
          f"critiques ; faux cas critiques {e['faux_critiques']} ; cas critiques manqués {e['critiques_manques']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("jeu", choices=[*JEUX, "tobi"])
    parser.add_argument("--graines", type=int, default=0, help="évaluer aussi N jeux de démonstration (1 à 5)")
    parser.add_argument("--json", type=Path, help="écrire les mesures dans ce fichier")
    args = parser.parse_args()
    sys.path.insert(0, str(RACINE))
    sys.path.insert(0, str(RACINE / "src"))
    from api.model import load_model

    logging.disable(logging.INFO)
    if args.jeu == "independant":
        print("Jeu indépendant : à lire seulement pour la mesure de départ et la mesure finale, jamais pour régler.\n")
    clf = load_model()
    lignes = lire_jeu(args.jeu)
    mesure = mesurer(clf, lignes)
    afficher(mesure, args.jeu)
    sortie = {"jeu": args.jeu, "modele": mesure}
    if args.graines:
        resultats = sur_plusieurs_graines(clf, lignes, GRAINES[: args.graines])
        print(f"\n== {args.jeu}, {len(resultats)} graines du jeu de démonstration (moyenne ± écart type)")
        for libelle, cle in [("exactitude", ("categorie", "exactitude")), ("F1 macro", ("categorie", "f1_macro")),
                             ("abstention", ("categorie", "abstention")),
                             ("exactitude quand il répond", ("categorie", "exactitude_quand_repond")),
                             ("priorité exacte", ("priorite", "exactitude")), ("escalade", ("escalade", "taux")),
                             ("fausses escalades", ("escalade", "fausses_escalades"))]:
            valeurs = [r[cle[0]][cle[1]] for r in resultats if r[cle[0]][cle[1]] is not None]
            if valeurs:
                print(f"{libelle:>28} : {moyenne_ecart(valeurs)}")
        faux = [r["categorie"]["faux"] for r in resultats]
        print(f"{'faux (catégorie)':>28} : {statistics.mean(faux):.1f} (de {min(faux)} à {max(faux)})")
        sortie["graines"] = resultats
    if args.json:
        args.json.write_text(json.dumps(sortie, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
