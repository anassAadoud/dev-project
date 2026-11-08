"""Le jeu d'évaluation (TP5.1) : 94 messages jamais utilisés pour écrire la base ni le jeu de démonstration.

Ces seuils suivent les chiffres mesurés au TP5.1 (63 justes, 5 faux, hors sujet 10 sur 10) :
le test échoue si une modification du modèle, de la base ou des seuils fait reculer l'agent.
"""
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
MODELE = RACINE / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")
sys.path.insert(0, str(RACINE / "src"))
from bilan_evaluation import CATEGORIES, evaluer, lire_jeu  # noqa: E402

MINIMUM_JUSTES, MAXIMUM_FAUX = 60, 5


@pytest.fixture(scope="module")
def bilan():
    from api.model import load_model

    return evaluer(load_model(), lire_jeu())


def test_jeu_complet():
    lignes = lire_jeu()
    assert len(lignes) == 94
    for categorie in CATEGORIES:
        assert sum(ligne["attendu"] == categorie for ligne in lignes) == 12
    assert sum(ligne["attendu"] == "hors_sujet" for ligne in lignes) == 10


def test_assez_de_reponses_justes(bilan):
    assert bilan["total"]["juste"] >= MINIMUM_JUSTES, bilan["total"]


def test_peu_d_erreurs_franches(bilan):
    assert bilan["total"]["faux"] <= MAXIMUM_FAUX, bilan["total"]


def test_tout_le_hors_sujet_va_au_tri(bilan):
    assert bilan["hors_sujet"]["faux"] == 0, bilan["hors_sujet"]


def test_aucune_categorie_oubliee(bilan):
    """Chaque catégorie a au moins quatre réponses justes sur douze."""
    for categorie in CATEGORIES:
        assert bilan[categorie]["juste"] >= 4, (categorie, bilan[categorie])
