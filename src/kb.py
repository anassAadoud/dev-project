#!/usr/bin/env python
"""La base de connaissances : trouver l'article qui correspond à un incident (TP3).

La partie « recherche » d'un RAG, sans génération : similarité cosinus TF-IDF entre
l'incident et le titre + les symptômes de chaque article de la même catégorie.
Sous SEUIL_SIMILARITE, aucun article n'est proposé : l'agent pose une question de précision.
TP5.2 : la recherche se fait dans TOUTE la base (proposer), la catégorie prédite donnant un bonus de score :
si le classifieur se trompe, le bon article apparaît quand même. Index de recherche : mots + caractères.
Mesuré sur la validation (105 incidents, src/evaluer_articles.py) : top-1 52 % -> 75 %, top-3 58 % -> 86 % ;
une réponse au diagnostic : top-1 79 % (docs/semaine5.2.md).
Le second avis de classement (article_le_plus_proche) garde l'index de mots, sur lequel SEUIL_BASE est réglé.
TP5.1 : on peut exclure les articles déjà essayés (deuxième proposition), et classer les
catégories selon leur meilleur article (l'ordre des boutons quand le modèle hésite).

Usage :
  python src/kb.py reseau "My VPN keeps disconnecting every 10 minutes"
  >>> from kb import chercher ; chercher("texte", "reseau")
"""
import csv
import sys
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion

RACINE = Path(__file__).resolve().parents[1]
BASE = RACINE / "data" / "base_connaissances.csv"
SEUIL_SIMILARITE = 0.10  # en dessous, l'article ne parle pas de cet incident
COLONNES = ["id", "categorie", "titre", "symptomes", "etapes", "escalade_si"]  # « source » est facultative
BONUS_CATEGORIE = 0.10  # validation : bonus 0 -> top-1 67 %, 0,05 -> 71 %, 0,10 à 0,30 -> 73 % (mots seuls)
NB_PROPOSES = 3
CATEGORIES = ["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]


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


def _similarites(texte: str) -> tuple[list[dict[str, str]], list[float]]:
    articles, vectoriseur, matrice = charger_base()
    return articles, [float(s) for s in cosine_similarity(vectoriseur.transform([texte]), matrice)[0]]


def mode_phrases() -> str | None:
    """Le mode des vecteurs de phrases du modèle servi (minilm, factice), ou None : la recherche suit le modèle."""
    from encodeur import mode_du_modele
    from predict import charger_modele

    try:
        return mode_du_modele(charger_modele()["categorie"])
    except FileNotFoundError:
        return None


@lru_cache(maxsize=1)
def charger_index_recherche() -> tuple[FeatureUnion, object]:
    """L'index de recherche des articles (TP5.2) : mots et n-grammes de caractères (fautes, formes voisines) ;
    phase 4 : et les vecteurs de phrases quand le modèle servi en a (top-3 de la validation 85,7 % -> 96,2 %)."""
    from encodeur import Phrases

    articles = charger_base()[0]
    parties = [
        ("mots", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")),
        ("caracteres", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ]
    mode = mode_phrases()
    if mode is not None:
        parties.append(("phrases", Phrases(1.0, mode)))
    vectoriseur = FeatureUnion(parties)
    return vectoriseur, vectoriseur.fit_transform([f"{a['titre']} {a['symptomes']}" for a in articles])


def _fiche(article: dict[str, str], similarite: float) -> dict:
    return {
        "id": article["id"],
        "categorie": article["categorie"],
        "titre": article["titre"],
        "etapes": [e.strip() for e in article["etapes"].split("|") if e.strip()],
        "escalade_si": article["escalade_si"],
        "similarite": round(min(max(similarite, 0.0), 1.0), 3),
        "source": article.get("source") or None,
    }


def proposer(texte: str, categorie: str | None = None, nombre: int = NB_PROPOSES, exclus: Iterable[str] = (),
             preferes: Iterable[str] = ()) -> list[dict]:
    """Les meilleurs articles de toute la base, hors articles exclus. La catégorie prédite donne un bonus,
    les articles préférés (réponse à une question de diagnostic) passent devant. Sous SEUIL_SIMILARITE, rien."""
    from predict import est_vague  # la même règle que le classement : un message vague n'a pas d'article

    articles = charger_base()[0]
    vectoriseur, matrice = charger_index_recherche()
    deja, avant = set(exclus), list(preferes)
    if est_vague(texte, vectoriseur.transformer_list[0][1]) and not avant:
        return []  # « It's not working again » : l'agent demande des détails au lieu de deviner
    similarites = cosine_similarity(vectoriseur.transform([texte]), matrice)[0]
    candidats = []
    for i, article in enumerate(articles):
        if article["id"] in deja or (similarites[i] < SEUIL_SIMILARITE and article["id"] not in avant):
            continue
        score = float(similarites[i]) + (BONUS_CATEGORIE if article["categorie"] == categorie else 0.0)
        if article["id"] in avant:
            score += 10.0  # le diagnostic passe devant tout ; entre articles préférés, la similarité décide
        candidats.append((score, i))
    candidats.sort(reverse=True)
    return [_fiche(articles[i], float(similarites[i])) for _, i in candidats[:nombre]]


def chercher(texte: str, categorie: str, exclus: Iterable[str] = (), preferes: Iterable[str] = ()) -> dict | None:
    """Le meilleur article de toute la base (bonus pour la catégorie), hors exclus, ou None si aucun n'est proche."""
    trouves = proposer(texte, categorie, 1, exclus, preferes)
    return trouves[0] if trouves else None


def article_le_plus_proche(texte: str) -> tuple[str, float]:
    """La catégorie de l'article le plus proche du texte, toutes catégories confondues, et sa similarité.
    C'est le second avis de l'API quand le modèle hésite (TP5.1)."""
    articles, similarites = _similarites(texte)
    meilleur = max(range(len(articles)), key=lambda i: similarites[i])
    return articles[meilleur]["categorie"], round(similarites[meilleur], 3)


def categories_proches(texte: str) -> list[str]:
    """Les 7 catégories, de celle dont un article ressemble le plus au texte à la moins proche.
    À égalité (aucun mot commun), l'ordre de CATEGORIES est gardé."""
    articles, similarites = _similarites(texte)
    meilleure = dict.fromkeys(CATEGORIES, 0.0)
    for article, similarite in zip(articles, similarites, strict=True):
        if article["categorie"] in meilleure:
            meilleure[article["categorie"]] = max(meilleure[article["categorie"]], similarite)
    return sorted(CATEGORIES, key=lambda c: -meilleure[c])


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
