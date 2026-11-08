"""L'évaluation du TP5.2 : des jeux séparés, aucune fuite, des mesures justes.

Ces tests ne demandent pas de modèle : ils vérifient les jeux, le découpage honnête et les
fonctions de mesure. La CI les joue tous.
"""
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
import evaluer  # noqa: E402
import make_demo  # noqa: E402

NOMS = ["validation", "independant", "evaluation", "jeu_or", "conversations_30"]


def textes(nom):
    return {ligne["text"].strip().lower() for ligne in evaluer.lire_jeu(nom)}


@pytest.mark.parametrize("nom, par_categorie, hors_sujet", [("validation", 15, 15), ("independant", 16, 14)])
def test_jeux_complets_et_equilibres(nom, par_categorie, hors_sujet):
    lignes = evaluer.lire_jeu(nom)
    for categorie in evaluer.CATEGORIES:
        assert sum(ligne["attendu"] == categorie for ligne in lignes) == par_categorie, categorie
    assert sum(ligne["attendu"] == "hors_sujet" for ligne in lignes) == hors_sujet
    for ligne in lignes:  # chaque incident a sa priorité attendue, le hors sujet n'en a pas
        attendue = {"high", "medium", "low"} if ligne["attendu"] in evaluer.CATEGORIES else {""}
        assert ligne["priorite"] in attendue, ligne


@pytest.mark.parametrize("a, b", [(a, b) for i, a in enumerate(NOMS) for b in NOMS[i + 1:]])
def test_aucun_message_commun_entre_deux_jeux(a, b):
    assert not textes(a) & textes(b), (a, b)


@pytest.mark.parametrize("nom", NOMS)
def test_aucun_message_d_un_jeu_dans_l_entrainement(nom):
    """Le jeu de démonstration et la base ne contiennent aucun message des jeux de mesure."""
    entrainement = {ligne[0].strip().lower() for ligne in make_demo.generer(make_demo.GRAINE)}
    symptomes = {s.lower() for liste in make_demo.tous_les_symptomes().values() for s in liste}
    assert not textes(nom) & entrainement
    assert not {t.rstrip(".!?") for t in textes(nom)} & symptomes


def test_generer_est_reproductible_et_groupe():
    a, b = make_demo.generer(7), make_demo.generer(7)
    assert a == b and all(len(ligne) == 4 for ligne in a)
    assert make_demo.generer(8) != a
    assert all(ligne[3].split(":")[0] == ligne[1] for ligne in a)  # le groupe nomme la catégorie du symptôme


def test_decoupage_par_groupe_sans_fuite():
    import pandas as pd

    import train

    df = pd.DataFrame(make_demo.generer(make_demo.GRAINE), columns=["text", "categorie", "priorite", "groupe"])
    entr, test = train.decouper_par_groupe(df)
    assert not set(entr["groupe"]) & set(test["groupe"])
    assert 0.1 < len(test) / len(df) < 0.35
    sans_groupe = df.drop(columns="groupe")
    assert len(train.decouper_par_groupe(sans_groupe)[1]) == len(train.decouper(sans_groupe)[1])
    assert train.f1_par_groupe(sans_groupe) is None


def test_ece():
    assert evaluer.ece([0.9, 0.9, 0.9, 0.9], [True, True, True, True]) == pytest.approx(0.1)
    assert evaluer.ece([0.55, 0.55], [True, False]) == pytest.approx(0.05)


def test_f1_par_classe_compte_l_abstention_comme_un_oubli():
    vrais = ["reseau", "reseau", "materiel", "materiel"]
    predits = ["reseau", "INDETERMINE", "materiel", "reseau"]
    m = evaluer.f1_par_classe(vrais, predits)
    assert m["reseau"]["precision"] == 0.5 and m["reseau"]["rappel"] == 0.5
    assert m["materiel"]["precision"] == 1.0 and m["materiel"]["rappel"] == 0.5
    assert m["securite"] == {"precision": 0.0, "rappel": 0.0, "f1": 0.0, "support": 0}


def test_mesurer_avec_un_faux_classifier():
    """Les taux d'escalade, les faux cas critiques et le hors sujet, sur un classifier simulé."""

    class Faux:
        def assist(self, texte):
            label = {"a": "reseau", "b": "securite", "c": "INDETERMINE", "d": "panne_service"}[texte]
            critique = label in evaluer.CRITIQUES
            return {"label": label, "priorite": "medium", "decision": "escalade" if label != "reseau" else "solution",
                    "motif": "critique" if critique else ("confiance_basse" if label == "INDETERMINE" else "solution")}

    lignes = [{"text": "a", "attendu": "reseau", "priorite": "medium"},
              {"text": "b", "attendu": "reseau", "priorite": "low"},
              {"text": "c", "attendu": "hors_sujet", "priorite": ""},
              {"text": "d", "attendu": "panne_service", "priorite": "high"}]
    import predict

    original = predict.predict
    predict.predict = lambda t: {"label": "reseau", "score": 0.9, "priorite": "medium", "connus": 1.0}
    try:
        m = evaluer.mesurer(Faux(), lignes)
    finally:
        predict.predict = original
    assert m["categorie"]["exactitude"] == pytest.approx(2 / 3, abs=1e-3) and m["categorie"]["faux"] == 1
    assert m["hors_sujet_refuse"] == 1.0
    assert m["escalade"]["faux_critiques"] == 1      # « b » : réseau classé sécurité, escaladé comme critique
    assert m["escalade"]["fausses_escalades"] == 0.5  # un des deux incidents réseau part au technicien
    assert m["escalade"]["critiques_manques"] == 0
    assert m["priorite"]["exactitude"] == pytest.approx(1 / 3, abs=1e-3)
