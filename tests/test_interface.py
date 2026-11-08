"""Tests de la page Streamlit (TP5), avec l'outil de test de Streamlit (AppTest)."""
from pathlib import Path

import httpx
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from ui import client  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]
PAGE = str(RACINE / "ui" / "app.py")
pytestmark = pytest.mark.skipif(not (RACINE / "models" / "support.joblib").exists(),
                                reason="modèle non produit : python src/train.py")


@pytest.fixture(scope="module")
def api(tmp_path_factory):
    from fastapi.testclient import TestClient

    from api.main import app

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUPPORT_TICKETS", str(tmp_path_factory.mktemp("tickets") / "tickets.jsonl"))
        with TestClient(app) as c:
            yield c


@pytest.fixture
def page(api, monkeypatch):
    monkeypatch.setattr(client, "creer_session", lambda: api)  # la page parle à l'API en mémoire
    return AppTest.from_file(PAGE, default_timeout=30).run()


def aider(page, texte):
    page.text_area(key="texte").input(texte).run()
    page.button(key="aider").click().run()
    return page


def test_page_annonce_api_prete(page):
    assert "API ready" in page.caption[0].value


def test_solution_pas_a_pas_puis_resolu(page):
    page = aider(page, "The printer on the second floor shows offline and nothing prints, no rush")
    assert page.metric[0].label == "Hardware"
    assert len(page.checkbox) >= 3  # les étapes cochables de l'article
    page.radio(key="resolu").set_value("Yes").run()
    assert "closed" in page.success[0].value


def test_non_resolu_cree_un_ticket(page):
    page = aider(page, "The printer on the second floor shows offline and nothing prints, no rush")
    page.radio(key="resolu").set_value("No").run()
    assert "Ticket TCK-" in page.success[0].value and "Poste de travail" in page.success[0].value


def test_texte_inconnu_je_ne_sais_pas_puis_ticket(page):
    page = aider(page, "xqzvb wlkptr grombu")
    assert page.metric[0].label.startswith("I don't know")
    assert page.warning[0].value == client.MOTIFS["mots_inconnus"]
    page.button(key="creer").click().run()
    assert "Tri N1" in page.success[0].value


def test_espaces_avertissement(page):
    assert aider(page, "   ").warning[0].value == client.REFUS


def test_api_injoignable(monkeypatch):
    monkeypatch.setattr(client, "creer_session",
                        lambda: httpx.Client(base_url="http://127.0.0.1:9", timeout=1))
    page = AppTest.from_file(PAGE, default_timeout=30).run()
    assert page.error[0].value == client.INJOIGNABLE
