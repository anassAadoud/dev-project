#!/usr/bin/env python
"""Entraîne et sauvegarde les deux modèles de l'agent : catégorie IT et priorité.

Usage :
  python src/train.py           # jeu de démonstration (data/demo_incidents.csv)
  python src/train.py --reel    # vrai jeu public : Tobi-Bueck/customer-support-tickets

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
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

RACINE = Path(__file__).resolve().parents[1]
DEMO = RACINE / "data" / "demo_incidents.csv"
URL_REEL = (
    "https://huggingface.co/api/datasets/Tobi-Bueck/customer-support-tickets/"
    "parquet/default/train/0.parquet"
)
MODELE = RACINE / "models" / "support.joblib"
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


def charger(reel: bool) -> tuple[pd.DataFrame, str]:
    if reel:
        return preparer_reel(pd.read_parquet(URL_REEL)), "tobi-bueck"
    if not DEMO.exists():
        raise SystemExit("data/demo_incidents.csv absent : lancez d'abord python src/make_demo.py")
    return pd.read_csv(DEMO), "demo"


def tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)


def construire_pipeline() -> Pipeline:
    """Vectoriseur et modèle dans un seul objet : la même transformation
    s'applique forcément à l'entraînement et en production. LinearSVC calibré :
    le meilleur F1 du notebook, et une vraie probabilité pour l'abstention."""
    return Pipeline([
        ("tfidf", tfidf()),
        ("clf", CalibratedClassifierCV(LinearSVC(class_weight="balanced", random_state=GRAINE), cv=3)),
    ])


def construire_pipeline_priorite() -> Pipeline:
    """Le second modèle, comme la section 9 du notebook : régression logistique sur la priorité."""
    return Pipeline([
        ("tfidf", tfidf()),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=GRAINE)),
    ])


def decouper(df: pd.DataFrame):
    """Découper AVANT toute transformation : sinon le jeu de test fuite dans l'entraînement."""
    return train_test_split(df, test_size=0.2, random_state=GRAINE, stratify=df["categorie"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reel", action="store_true", help="utiliser le jeu public Tobi-Bueck")
    args = parser.parse_args()

    df, source = charger(args.reel)
    print(f"Source : {source}, {len(df)} incidents, {df['categorie'].nunique()} catégories")
    train, test = decouper(df)
    print(f"{len(train)} incidents d'entraînement, {len(test)} de test")

    pipeline = construire_pipeline().fit(train["text"], train["categorie"])
    print(f"Vocabulaire : {len(pipeline.named_steps['tfidf'].vocabulary_)} termes")
    rapport = classification_report(test["categorie"], pipeline.predict(test["text"]),
                                    output_dict=True, zero_division=0)
    f1 = rapport["macro avg"]["f1-score"]
    seuil = SEUILS_ACCEPTATION[source]
    print(f"F1 macro sur le jeu de test : {f1:.3f} (seuil du cours {SEUIL_F1} : "
          f"{'atteint' if f1 >= SEUIL_F1 else 'non atteint'} ; acceptation pour « {source} » : {seuil})")

    priorite = construire_pipeline_priorite().fit(train["text"], train["priorite"])
    rapport_p = classification_report(test["priorite"], priorite.predict(test["text"]),
                                      output_dict=True, zero_division=0)
    print(f"Priorité : F1 macro {rapport_p['macro avg']['f1-score']:.3f}, rappel de high {rapport_p['high']['recall']:.3f}")

    MODELE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"categorie": pipeline, "priorite": priorite}, MODELE)
    METRIQUES.write_text(json.dumps({
        "source": source,
        "date": date.today().isoformat(),
        "n_train": len(train),
        "n_test": len(test),
        "classes": [str(c) for c in pipeline.classes_],
        "f1_macro": round(f1, 4),
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
