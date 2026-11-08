"""Les 30 conversations du bilan des tickets (TP5.1), rejouées par l'API à chaque test.

Aucun ticket pour un incident que la base sait régler, un ticket pour chaque incident non
résolu, demandé ou critique, jamais de ticket au premier message, jamais deux par conversation.
"""
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
MODELE = RACINE / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")
sys.path.insert(0, str(RACINE / "src"))
from bilan_tickets import apres, lire_conversations, ticket_attendu  # noqa: E402

LIGNES = lire_conversations()


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from fastapi.testclient import TestClient

    from api.main import app

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUPPORT_TICKETS", str(tmp_path_factory.mktemp("bilan") / "tickets.jsonl"))
        mp.delenv("SUPPORT_LLM", raising=False)
        with TestClient(app) as c:
            yield c


def test_trente_conversations_variees():
    scenarios = {ligne["scenario"] for ligne in LIGNES}
    assert len(LIGNES) == 30 and scenarios == {"resolu", "non_resolu", "demande", "critique"}
    assert sum(ligne["scenario"] == "resolu" for ligne in LIGNES) > 15  # la plupart ont une solution


def test_chaque_incident_resolu_a_son_article_dans_la_base():
    from kb import charger_base

    ids = {a["id"] for a in charger_base()[0]}
    manquants = {i for ligne in LIGNES for i in ligne["articles_ok"].split()} - ids
    assert not manquants, f"articles absents de la base : {sorted(manquants)}"


@pytest.mark.parametrize("ligne", LIGNES, ids=[ligne["text"][:40] for ligne in LIGNES])
def test_un_ticket_seulement_si_necessaire(client, ligne):
    from kb import charger_base

    ids = {a["id"] for a in charger_base()[0]}
    n, tours, fin, codes = apres(ligne, client)
    assert codes[0] != "ticket_cree" and n <= 1
    if ligne["scenario"] != "resolu":
        assert n == 1, f"un ticket attendu ({ligne['scenario']}) : {codes}"
    elif set(ligne["articles_ok"].split()) & ids:  # la base contient l'article qui règle l'incident
        assert (n, fin) == (0, "résolu sans ticket"), f"ticket inutile : {codes}"
    assert n == ticket_attendu(ligne) or ligne["scenario"] == "resolu"
