"""TP5.2 : la priorité décidée à part, la règle des messages mêlés et la règle « tout le monde = panne ».

Sans modèle (sauf les deux derniers tests) : ces règles se vérifient partout, CI comprise.
"""
import csv
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
import priorite as P  # noqa: E402
from predict import partie_principale  # noqa: E402

MODELE = RACINE / "models" / "support.joblib"


@pytest.mark.parametrize("texte, attendu", [
    ("not urgent but the printer is offline", "low"),
    ("nothing urgent, just letting you know", "low"),
    ("no rush, whenever you can", "low"),
    ("it can wait until next week", "low"),
    ("low priority: the mouse is slow", "low"),
    ("URGENT: my account is locked", "high"),
    ("please fix it asap", "high"),
    ("the whole team is blocked", "high"),
    ("I have a client meeting in ten minutes", "high"),
    ("the report is due in one hour", "high"),
    ("all customers cannot pay", "high"),
    ("my mouse is slow", None),
])
def test_indices_de_priorite(texte, attendu):
    assert P.indice(texte) == attendu


@pytest.mark.parametrize("texte, categorie, repli, attendu", [
    ("the VPN drops", "reseau", "high", ("medium", "categorie")),       # sans indice : la catégorie
    ("someone logged into my account", "securite", "low", ("high", "categorie")),
    ("the ERP is slow", "panne_service", "low", ("high", "categorie")),
    ("not urgent, the ERP is slow", "panne_service", "high", ("low", "indice")),  # le calme passe avant
    ("something is wrong", None, "low", ("low", "modele")),             # catégorie inconnue : le modèle
    ("something is wrong", None, None, ("medium", "modele")),
])
def test_priorite_indice_puis_categorie_puis_modele(texte, categorie, repli, attendu):
    assert P.priorite(texte, categorie, repli) == attendu


@pytest.mark.parametrize("texte, attendu", [
    ("the whole company cannot send emails", True),
    ("Single sign-on is broken for every employee", True),
    ("nobody can open the ERP", True),
    ("my Outlook cannot send emails", False),
])
def test_impact_general(texte, attendu):
    assert P.impact_general(texte) is attendu


@pytest.mark.parametrize("texte, attendu", [
    ("The printer was fixed yesterday, but my account is locked since this morning",
     "my account is locked since this morning"),
    ("Not a hardware problem, the issue is that I was charged twice", "I was charged twice"),
    ("The screen was flickering, turns out it was a phishing pop-up", "a phishing pop-up"),
    ("Wi-Fi is fine now, however Outlook keeps crashing", "Outlook keeps crashing"),
])
def test_partie_principale_d_un_message_mele(texte, attendu):
    assert partie_principale(texte) == attendu


@pytest.mark.parametrize("texte", ["The VPN connects but I can't open the shared drive",
                                   "Outlook crashes but only when I open the calendar",
                                   "My VPN keeps disconnecting", "The issue is ok",
                                   "The issue is that my account is disabled after my leave"])
def test_les_pieges_ne_sont_pas_coupes(texte):
    assert partie_principale(texte) == texte


def test_jeu_des_melanges_complet():
    lignes = list(csv.DictReader((RACINE / "data" / "jeu_melanges.csv").open(encoding="utf-8")))
    assert len(lignes) == 36 and {ligne["type"] for ligne in lignes} == {"melange", "piege"}


@pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")
def test_la_regle_des_melanges_ne_fait_pas_reculer():
    """Sur les 36 messages variés : les messages mêlés gagnent, les pièges ne perdent rien."""
    from predict import charger_modele

    modele = charger_modele()["categorie"]
    lignes = list(csv.DictReader((RACINE / "data" / "jeu_melanges.csv").open(encoding="utf-8")))
    for type_ in ["melange", "piege"]:
        sous = [ligne for ligne in lignes if ligne["type"] == type_]
        sans = sum(modele.predict([ligne["text"]])[0] == ligne["attendu"] for ligne in sous)
        avec = sum(modele.predict([partie_principale(ligne["text"])])[0] == ligne["attendu"] for ligne in sous)
        assert avec >= sans, (type_, sans, avec)


@pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")
def test_api_priorite_et_panne_generale():
    from api.model import load_model

    clf = load_model()
    assert clf.predict("not urgent: my mouse is slow")["priorite"] == "low"
    assert clf.predict("URGENT the VPN keeps disconnecting, I have a client call in ten minutes")["priorite"] == "high"
    assert clf.predict("The whole company cannot send emails right now")["label"] == "panne_service"
