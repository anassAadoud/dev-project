#!/usr/bin/env python
"""La base de connaissances : trouver l'article qui correspond à un incident (TP3).

La partie « recherche » d'un RAG, sans génération : similarité cosinus TF-IDF entre
l'incident et le titre + les symptômes de chaque article de la même catégorie.
Sous SEUIL_SIMILARITE, aucun article n'est proposé : l'incident sera escaladé.

Usage :
  python src/kb.py reseau "My VPN keeps disconnecting every 10 minutes"
  >>> from kb import chercher ; chercher("texte", "reseau")
"""
import csv
import sys
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RACINE = Path(__file__).resolve().parents[1]
BASE = RACINE / "data" / "base_connaissances.csv"
SEUIL_SIMILARITE = 0.10  # en dessous, l'article ne parle pas de cet incident
COLONNES = ["id", "categorie", "titre", "symptomes", "etapes", "escalade_si"]


@lru_cache(maxsize=1)
def charger_base() -> tuple[list[dict[str, str]], TfidfVectorizer, object]:
    """Lue et indexée une seule fois par processus, comme le modèle."""
    if not BASE.exists():
        raise FileNotFoundError(f"base de connaissances introuvable : {BASE}")
    with BASE.open(encoding="utf-8", newline="") as f:
        articles = list(csv.DictReader(f))
    manquantes = set(COLONNES) - set(articles[0] if articles else {})
    if manquantes:
        raise ValueError(f"colonnes absentes de la base : {sorted(manquantes)}")
    vectoriseur = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
    matrice = vectoriseur.fit_transform([f"{a['titre']} {a['symptomes']}" for a in articles])
    return articles, vectoriseur, matrice


def chercher(texte: str, categorie: str) -> dict | None:
    """Le meilleur article de la catégorie, ou None si aucun n'est assez proche."""
    articles, vectoriseur, matrice = charger_base()
    similarites = cosine_similarity(vectoriseur.transform([texte]), matrice)[0]
    candidats = [i for i, a in enumerate(articles) if a["categorie"] == categorie]
    if not candidats:
        return None
    meilleur = max(candidats, key=lambda i: similarites[i])
    if similarites[meilleur] < SEUIL_SIMILARITE:
        return None
    article = articles[meilleur]
    return {
        "id": article["id"],
        "titre": article["titre"],
        "etapes": [e.strip() for e in article["etapes"].split("|") if e.strip()],
        "escalade_si": article["escalade_si"],
        "similarite": round(float(similarites[meilleur]), 3),
    }


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    article = chercher(" ".join(sys.argv[2:]), sys.argv[1])
    if article is None:
        print("Aucun article assez proche : escalade.")
        return 0
    print(f"{article['id']} {article['titre']} (similarité {article['similarite']})")
    for numero, etape in enumerate(article["etapes"], start=1):
        print(f"  {numero}. {etape}")
    print(f"  Escalader si : {article['escalade_si']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
