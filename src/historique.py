#!/usr/bin/env python
"""Le ticket passé le plus semblable, et ce qui l'a réglé (TP5.1).

Deux sources de tickets passés :
  - les tickets de l'agent qu'un technicien a résolus (statut « resolu » ou « ferme », avec
    une résolution) : l'agent apprend de ses propres escalades ;
  - l'historique Tobi-Bueck (data/historique.csv), si on l'a construit : la réponse (`answer`)
    du support pour chaque incident. Hors Git, comme toutes les données brutes.
La recherche est la même que celle de la base : similarité cosinus TF-IDF, dans la même
catégorie quand elle est connue. Sous SEUIL_SEMBLABLE, rien n'est montré.

Usage :
  python src/historique.py --reel        # construit data/historique.csv à partir de Tobi-Bueck
  >>> from historique import plus_semblable
"""
import argparse
import csv
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RACINE = Path(__file__).resolve().parents[1]
HISTORIQUE = RACINE / "data" / "historique.csv"
SEUIL_SEMBLABLE = 0.30  # en dessous, le ticket passé parle d'autre chose (mesuré sur Tobi-Bueck : docs/semaine5.1.md)
LONGUEUR_REPONSE = 600


@lru_cache(maxsize=1)
def charger_historique() -> tuple[dict[str, str], ...]:
    """Les tickets passés de data/historique.csv, ou rien si le fichier n'a pas été construit."""
    if not HISTORIQUE.exists():
        return ()
    with HISTORIQUE.open(encoding="utf-8", newline="") as f:
        return tuple({"id": f"TB-{i:05d}", "text": ligne["text"], "categorie": ligne["categorie"],
                      "resolution": ligne["answer"], "source": "Tobi-Bueck history"}
                     for i, ligne in enumerate(csv.DictReader(f)) if ligne.get("answer"))


def plus_semblable(texte: str, passes: list[dict], categorie: str | None = None) -> dict | None:
    """Le ticket passé le plus proche du texte (de la même catégorie si elle est connue), ou None."""
    candidats = [p for p in passes if p.get("resolution") and (categorie is None or p.get("categorie") == categorie)]
    if not candidats or not texte.strip():
        return None
    vectoriseur = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
    try:
        matrice = vectoriseur.fit_transform([p["text"] for p in candidats])
    except ValueError:  # aucun mot utile dans les tickets passés
        return None
    similarites = cosine_similarity(vectoriseur.transform([texte]), matrice)[0]
    meilleur = int(similarites.argmax())
    if similarites[meilleur] < SEUIL_SEMBLABLE:
        return None
    passe = candidats[meilleur]
    return {"id": passe["id"], "text": passe["text"][:300], "resolution": passe["resolution"][:LONGUEUR_REPONSE],
            "similarite": round(float(similarites[meilleur]), 3), "source": passe["source"]}


def construire_reel() -> int:
    """Télécharge Tobi-Bueck, applique les filtres de train.py et garde la réponse du support."""
    import pandas as pd

    from train import URL_REEL, preparer_reel

    df = preparer_reel(pd.read_parquet(URL_REEL)).dropna(subset=["answer"])
    HISTORIQUE.parent.mkdir(parents=True, exist_ok=True)
    df[["text", "categorie", "answer"]].to_csv(HISTORIQUE, index=False)
    print(f"{len(df)} tickets passés écrits dans {HISTORIQUE.relative_to(RACINE).as_posix()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reel", action="store_true", help="construire data/historique.csv depuis Tobi-Bueck")
    if not parser.parse_args().reel:
        parser.print_help()
        return 2
    return construire_reel()


if __name__ == "__main__":
    raise SystemExit(main())
