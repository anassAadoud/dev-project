"""Tests du modèle du TP2.

Deux tests lisent models/metrics.json, qui est versionné dans Git : ils tournent
donc aussi dans la CI, où le modèle lui-même n'existe pas. Les deux autres sont
ignorés tant que models/support.joblib n'a pas été produit sur le poste.
"""
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
METRIQUES = RACINE / "models" / "metrics.json"
MODELE = RACINE / "models" / "support.joblib"
CATEGORIES = {"securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"}
# Seuils d'acceptation de la fiche cas2 : 0,85 (cours) sur la démonstration, 0,75 sur Tobi-Bueck.
SEUILS_F1 = {"demo": 0.85, "tobi-bueck": 0.75}

sys.path.insert(0, str(RACINE / "src"))


def lire_metriques() -> dict:
    """Lue dans le test lui-même : un fichier absent donne un échec lisible."""
    assert METRIQUES.exists(), "models/metrics.json absent : lancez python src/train.py"
    return json.loads(METRIQUES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def predicteur():
    if not MODELE.exists():
        pytest.skip("models/support.joblib absent sur ce poste (normal en CI)")
    from predict import predict
    return predict


def test_metriques_completes():
    metriques = lire_metriques()
    for cle in ["source", "f1_macro", "accuracy", "rappel_par_classe", "priorite_f1_macro", "n_train", "n_test"]:
        assert cle in metriques, f"clé absente de metrics.json : {cle}"
    assert metriques["n_test"] > 0
    assert set(metriques["classes"]) == CATEGORIES


def test_f1_au_dessus_du_seuil():
    metriques = lire_metriques()
    f1, seuil = metriques["f1_macro"], SEUILS_F1[metriques["source"]]
    assert f1 >= seuil, f"F1 macro {f1} sous le seuil {seuil} ({metriques['source']}) : réentraînez ou améliorez le modèle"


def test_prediction_evidente(predicteur):
    assert predicteur("My VPN keeps disconnecting and the network is unstable")["label"] == "reseau"
    assert predicteur("I was charged twice and the invoice shows the wrong amount")["label"] == "facturation"


def test_format_de_sortie(predicteur):
    sortie = predicteur("The printer shows offline and nothing prints")
    # inclusion et non égalité : predict() peut renvoyer des champs supplémentaires
    assert {"label", "score", "priorite"} <= set(sortie)
    assert sortie["label"] in CATEGORIES
    assert sortie["priorite"] in {"high", "medium", "low"}
    assert 0.0 <= sortie["score"] <= 1.0
    with pytest.raises(ValueError):
        predicteur("   ")
