#!/usr/bin/env python
"""Entraîne et sauvegarde les deux modèles de l'agent : catégorie IT et priorité.

Usage :
  python src/train.py            # jeu de démonstration (data/demo_incidents.csv) : celui de la CI
  python src/train.py --mixte    # TP5.2 : démonstration + tickets réels Tobi-Bueck raccourcis et pondérés
  python src/train.py --origine  # TP5.2 : le modèle d'origine (mots seuls), gardé comme repli
  python src/train.py --sans-minilm  # TP5.2 : mots + caractères, sans vecteurs de phrases (repli de l'hybride)
  SUPPORT_ENCODEUR=factice python src/train.py  # l'hybride avec un encodeur factice, sans téléchargement (CI)
  python src/train.py --reel     # vrai jeu public seul : Tobi-Bueck/customer-support-tickets

Produit : models/support.joblib (les deux modèles) et models/metrics.json
"""
import argparse
import json
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from encodeur import Phrases, mode_demande
from predict import vectoriseur_mots

RACINE = Path(__file__).resolve().parents[1]
DEMO = RACINE / "data" / "demo_incidents.csv"
URL_REEL = (
    "https://huggingface.co/api/datasets/Tobi-Bueck/customer-support-tickets/"
    "parquet/default/train/0.parquet"
)
MODELE = RACINE / "models" / "support.joblib"
# TP5.2 : copie locale du jeu réel (hors Git, comme data/*) : le second lancement marche hors ligne.
REEL_LOCAL = RACINE / "data" / "tobi_bueck.parquet"
METRIQUES = RACINE / "models" / "metrics.json"
SEUIL_F1 = 0.85       # le seuil du cours
# Seuil d'acceptation de notre fiche de cadrage (cas2), par source : le cours sur la démonstration ;
# sur Tobi-Bueck, 0,75 (référence du notebook : 0,788, étiquettes construites à partir des tags).
SEUILS_ACCEPTATION = {"demo": SEUIL_F1, "tobi-bueck": 0.75}
GRAINE = 42
CATEGORIES = ["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]
PRIORITES = ["high", "medium", "low"]

# Section 15.2 du notebook : la première règle qui correspond aux tags du ticket donne sa catégorie.
REGLES_TAGS = [
    ("securite", {"Security", "Virus", "Breach", "Malware", "Phishing"}),
    ("reseau", {"Network", "Connectivity", "VPN"}),
    ("materiel", {"Hardware", "Printer", "Device"}),
    ("compte_acces", {"Account", "Login", "Access", "Password"}),
    ("facturation", {"Billing", "Payment", "Refund", "Invoice"}),
    ("logiciel", {"Software", "Bug", "Crash", "Update"}),
    ("panne_service", {"Outage", "Disruption", "Maintenance"}),
]


def categorie_depuis_tags(tags: list) -> str | None:
    presents = {str(t).strip() for t in tags if pd.notna(t)}
    for categorie, mots in REGLES_TAGS:
        if presents & mots:
            return categorie
    return None


def preparer_reel(brut: pd.DataFrame) -> pd.DataFrame:
    """Les filtres du notebook : anglais, incidents, sujet + corps, doublons retirés, catégorie tirée des tags."""
    df = brut.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for colonne in ["language", "type", "priority"]:
        df[colonne] = df[colonne].astype("string").str.strip().str.lower()
    df = df[(df["language"] == "en") & (df["type"] == "incident")]
    df["text"] = (df["subject"].fillna("") + " " + df["body"].fillna("")).str.strip()
    df = df[df["text"].str.split().str.len() >= 3].drop_duplicates(subset="text")
    colonnes_tags = [c for c in df.columns if c.startswith("tag_")]
    df["categorie"] = [categorie_depuis_tags(list(ligne)) for ligne in df[colonnes_tags].itertuples(index=False)]
    df["priorite"] = df["priority"].replace({"critical": "high", "very_low": "low"})
    df = df.dropna(subset=["categorie"])
    df = df[df["priorite"].isin(PRIORITES)]
    return df[["text", "categorie", "priorite", "answer"]].reset_index(drop=True)


def lire_reel_brut() -> pd.DataFrame:
    """Le parquet Tobi-Bueck : la copie locale si elle existe, sinon le téléchargement, gardé ensuite."""
    if REEL_LOCAL.exists():
        return pd.read_parquet(REEL_LOCAL)
    brut = pd.read_parquet(URL_REEL)
    REEL_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    brut.to_parquet(REEL_LOCAL)
    return brut


def charger(reel: bool) -> tuple[pd.DataFrame, str]:
    if reel:
        return preparer_reel(lire_reel_brut()), "tobi-bueck"
    if not DEMO.exists():
        raise SystemExit("data/demo_incidents.csv absent : lancez d'abord python src/make_demo.py")
    return pd.read_csv(DEMO), "demo"


def tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)


# TP5.2 : n-grammes de caractères en plus des mots (fautes de frappe, mots jamais vus) ; mesuré sur la
# validation, 3 graines : exactitude 0,511 -> 0,559 (avec la réécriture et les applications : 0,635).
CARACTERES = True
# TP5.2 : le mode --mixte ajoute les tickets réels, raccourcis à la longueur d'un message et pondérés :
# F1 sur la validation de Tobi-Bueck 0,30 -> 0,67, mais deux fois plus d'erreurs franches sur les
# messages courts (poids 0,05 à 0,40 essayés ; 0,15 retenu). Voir docs/semaine5.2.md.
POIDS_REEL = 0.15
MOTS_REEL = 25


# TP5.2, phase 4 : l'hybride. Les vecteurs all-MiniLM-L6-v2 s'ajoutent aux TF-IDF (python src/essai_minilm.py) :
# validation, 3 graines, F1 macro 0,791 -> 0,847, faux 4,3 -> 3,0 ; poids 0,5 : 0,828 ; poids 2 : 0,850 (dans
# l'écart entre graines) : 1,0 est gardé. MiniLM seul perdait 5 points dans le notebook : il n'est pas essayé seul.
PHRASES = True
POIDS_PHRASES = 1.0


def tfidf_caracteres() -> TfidfVectorizer:
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)


def construire_pipeline(caracteres: bool | None = None, phrases: bool | None = None) -> Pipeline:
    """Vectoriseur et modèle dans un seul objet : la même transformation
    s'applique forcément à l'entraînement et en production. LinearSVC calibré :
    le meilleur F1 du notebook, et une vraie probabilité pour l'abstention.
    TP5.2 : avec caracteres, les mots et les n-grammes de caractères sont assemblés ; sans, c'est le
    modèle d'origine (TP2), gardé comme repli (python src/train.py --origine)."""
    caracteres = CARACTERES if caracteres is None else caracteres
    phrases = PHRASES if phrases is None else phrases
    parties = [("mots", tfidf()), ("caracteres", tfidf_caracteres())]
    if phrases:
        parties.append(("phrases", Phrases(POIDS_PHRASES, mode_demande())))
    vectoriseur = FeatureUnion(parties) if caracteres else tfidf()
    return Pipeline([
        ("tfidf", vectoriseur),
        ("clf", CalibratedClassifierCV(LinearSVC(class_weight="balanced", random_state=GRAINE), cv=3)),
    ])


def textes_courts(textes: pd.Series) -> pd.Series:
    """Un ticket réel raccourci à ses premiers mots : la longueur d'un message de l'agent."""
    return textes.map(lambda t: " ".join(str(t).split()[:MOTS_REEL]))


def reel_pour_le_melange() -> pd.DataFrame:
    """La partie entraînement de Tobi-Bueck (la partie test reste fermée), textes raccourcis."""
    reel, _ = charger(reel=True)
    entr, _ = decouper(reel)
    return entr.assign(text=textes_courts(entr["text"]))[["text", "categorie", "priorite"]]


def entrainer(entr: pd.DataFrame, reel: pd.DataFrame | None = None, caracteres: bool | None = None,
              phrases: bool | None = None) -> dict:
    """Les deux modèles servis par l'API. Avec reel, ses tickets s'ajoutent à la catégorie avec POIDS_REEL."""
    donnees, poids = entr[["text", "categorie"]], [1.0] * len(entr)
    if reel is not None:
        donnees = pd.concat([donnees, reel[["text", "categorie"]]])
        poids += [POIDS_REEL] * len(reel)
    categorie = construire_pipeline(caracteres, phrases).fit(donnees["text"], donnees["categorie"],
                                                             clf__sample_weight=poids)
    return {"categorie": categorie, "priorite": construire_pipeline_priorite().fit(entr["text"], entr["priorite"])}


def construire_pipeline_priorite() -> Pipeline:
    """Le second modèle, comme la section 9 du notebook : régression logistique sur la priorité."""
    return Pipeline([
        ("tfidf", tfidf()),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=GRAINE)),
    ])


def decouper(df: pd.DataFrame):
    """Découper AVANT toute transformation : sinon le jeu de test fuite dans l'entraînement."""
    return train_test_split(df, test_size=0.2, random_state=GRAINE, stratify=df["categorie"])


def decouper_par_groupe(df: pd.DataFrame):
    """TP5.2 : le découpage honnête du jeu de démonstration. Toutes les phrases d'un même symptôme
    vont du même côté : le test mesure la généralisation à des symptômes jamais vus."""
    if "groupe" not in df.columns:
        return decouper(df)
    i_train, i_test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=GRAINE)
                           .split(df, groups=df["groupe"]))
    return df.iloc[i_train], df.iloc[i_test]


def f1_par_groupe(df: pd.DataFrame, caracteres: bool | None = None, phrases: bool | None = None) -> float | None:
    """F1 macro d'un modèle entraîné sans les symptômes du test (None sans colonne groupe)."""
    if "groupe" not in df.columns:
        return None
    entr, test = decouper_par_groupe(df)
    modele = construire_pipeline(caracteres, phrases).fit(entr["text"], entr["categorie"])
    rapport = classification_report(test["categorie"], modele.predict(test["text"]), output_dict=True, zero_division=0)
    return round(rapport["macro avg"]["f1-score"], 4)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reel", action="store_true", help="utiliser le jeu public Tobi-Bueck")
    parser.add_argument("--mixte", action="store_true", help="démonstration + tickets réels raccourcis et pondérés")
    parser.add_argument("--origine", action="store_true", help="le modèle d'origine (mots seuls), comme repli")
    parser.add_argument("--sans-minilm", action="store_true", help="sans vecteurs de phrases (repli de l'hybride)")
    args = parser.parse_args()
    if args.reel and args.mixte:
        raise SystemExit("--reel et --mixte sont exclusifs")

    df, source = charger(args.reel)
    print(f"Source : {source}, {len(df)} incidents, {df['categorie'].nunique()} catégories")
    train, test = decouper(df)
    print(f"{len(train)} incidents d'entraînement, {len(test)} de test")

    reel = reel_pour_le_melange() if args.mixte else None
    if reel is not None:
        print(f"Mélange : {len(reel)} tickets réels raccourcis à {MOTS_REEL} mots, poids {POIDS_REEL}")
    phrases = False if (args.origine or args.sans_minilm) else None
    modeles = entrainer(train, reel, caracteres=False if args.origine else None, phrases=phrases)
    pipeline = modeles["categorie"]
    print(f"Vocabulaire : {len(vectoriseur_mots(pipeline).vocabulary_)} mots")
    rapport = classification_report(test["categorie"], pipeline.predict(test["text"]),
                                    output_dict=True, zero_division=0)
    f1 = rapport["macro avg"]["f1-score"]
    seuil = SEUILS_ACCEPTATION[source]
    print(f"F1 macro sur le jeu de test : {f1:.3f} (seuil du cours {SEUIL_F1} : "
          f"{'atteint' if f1 >= SEUIL_F1 else 'non atteint'} ; acceptation pour « {source} » : {seuil})")

    f1_groupe = f1_par_groupe(df, caracteres=False if args.origine else None, phrases=phrases)
    if f1_groupe is not None:
        print(f"F1 macro honnête (symptômes du test jamais vus à l'entraînement) : {f1_groupe:.3f}")

    priorite = modeles["priorite"]
    rapport_p = classification_report(test["priorite"], priorite.predict(test["text"]),
                                      output_dict=True, zero_division=0)
    print(f"Priorité : F1 macro {rapport_p['macro avg']['f1-score']:.3f}, rappel de high {rapport_p['high']['recall']:.3f}")

    MODELE.parent.mkdir(parents=True, exist_ok=True)
    variante = "origine (mots)" if args.origine else ("mots + caractères" if CARACTERES else "mots")
    if not args.origine and (PHRASES if phrases is None else phrases):
        variante += f" + phrases ({mode_demande()})"
    print(f"Variante : {variante}")
    meta = {"source": source, "variante": variante, "mixte": bool(args.mixte), "date": date.today().isoformat(),
            "f1_macro": round(f1, 4), "f1_macro_par_groupe": f1_groupe}
    joblib.dump({"categorie": pipeline, "priorite": priorite, "meta": meta}, MODELE)
    METRIQUES.write_text(json.dumps({
        "source": source,
        "variante": variante,
        "mixte": bool(args.mixte),
        "poids_reel": POIDS_REEL if args.mixte else None,
        "date": date.today().isoformat(),
        "n_train": len(train),
        "n_test": len(test),
        "classes": [str(c) for c in pipeline.classes_],
        "f1_macro": round(f1, 4),
        "f1_macro_par_groupe": f1_groupe,
        "accuracy": round(rapport["accuracy"], 4),
        "rappel_par_classe": {c: round(rapport[c]["recall"], 4) for c in CATEGORIES if c in rapport},
        "priorite_f1_macro": round(rapport_p["macro avg"]["f1-score"], 4),
        "priorite_rappel_high": round(rapport_p["high"]["recall"], 4),
        "seuil_f1": seuil,
        "seuil_f1_cours": SEUIL_F1,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Modèle : {MODELE.relative_to(RACINE).as_posix()}")
    print(f"Métriques : {METRIQUES.relative_to(RACINE).as_posix()} (versionné dans Git, contrairement au modèle)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
