"""Tests de la page Streamlit (TP5, conversation au TP5.1), avec l'outil de test de Streamlit (AppTest)."""
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
IMPRIMANTE = "The printer on the second floor shows offline and nothing prints, no rush"


@pytest.fixture
def api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setenv("SUPPORT_TICKETS", str(tmp_path / "tickets.jsonl"))
    monkeypatch.delenv("SUPPORT_LLM", raising=False)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def page(api, monkeypatch):
    monkeypatch.setattr(client, "creer_session", lambda: api)  # la page parle à l'API en mémoire
    return AppTest.from_file(PAGE, default_timeout=30).run()


def ecrire(page, texte):
    return page.chat_input(key="saisie").set_value(texte).run()


def dernier_message(page):
    return " ".join(m.value for m in page.chat_message[-1].markdown)


def cles_des_boutons(page):
    return {b.key for b in page.button}


def test_page_annonce_api_prete(page):
    assert "API ready" in page.sidebar.caption[0].value
    assert "Describe your IT problem" in dernier_message(page)


def test_solution_pas_a_pas_puis_resolu_sans_ticket(page):
    page = ecrire(page, IMPRIMANTE)
    assert client.REPLIQUES["solution"] in dernier_message(page)
    assert len(page.checkbox) >= 3  # les étapes cochables de l'article
    assert {"resolu", "pas_resolu", "demander_ticket"} <= cles_des_boutons(page)
    page.button(key="resolu").click().run()
    assert client.REPLIQUES["resolu"] in dernier_message(page)
    assert not [s for s in page.success if "Ticket" in s.value]


def test_pas_resolu_deux_fois_puis_ticket_confirme(page):
    page = ecrire(page, IMPRIMANTE)
    for _ in range(4):
        if "confirmer_ticket" in cles_des_boutons(page):
            break
        if "pas_resolu" in cles_des_boutons(page):
            page.checkbox[0].check().run()
            page.button(key="pas_resolu").click().run()
        else:
            page = ecrire(page, "The printer still shows offline")
    assert not [s for s in page.success if "Ticket" in s.value]  # proposé, pas encore créé
    page.button(key="confirmer_ticket").click().run()
    ticket = [s.value for s in page.success if "Ticket" in s.value]
    assert ticket and "Workstation" in ticket[0]
    # Le suivi : l'identifiant est déjà dans le champ, il suffit de cliquer.
    assert page.text_input(key="suivi_id").value.startswith("TCK-")
    page.button(key="suivre").click().run()
    assert page.text_input(key="suivi_id").value in page.subheader[0].value and "Open" in page.subheader[0].value


def test_texte_inconnu_boutons_de_categories(page):
    page = ecrire(page, "xqzvb wlkptr grombu")
    assert client.REPLIQUES["reformuler"] in dernier_message(page)
    assert {"cat-materiel", "cat-reseau", "cat-securite"} <= cles_des_boutons(page)
    page.button(key="cat-materiel").click().run()
    assert "Hardware" in " ".join(m.value for m in page.chat_message[-2].markdown)  # le choix de l'utilisateur


def test_avis_pouce_leve(page):
    page = ecrire(page, IMPRIMANTE)
    cle = next(k for k in cles_des_boutons(page) if k and k.startswith("avis-") and k.endswith("-haut"))
    page.button(key=cle).click().run()
    assert any("Thanks for your feedback" in c.value for c in page.caption)


def test_statistiques(page):
    page = ecrire(page, IMPRIMANTE)
    page.button(key="resolu").click().run()
    metriques = {m.label: m.value for m in page.metric}
    assert metriques["Solved without a ticket"] == "100%" and metriques["Conversations"] == "1"


def test_nouvelle_conversation(page):
    page = ecrire(page, IMPRIMANTE)
    page.button(key="nouvelle").click().run()
    assert "Describe your IT problem" in dernier_message(page) and len(page.chat_message) == 1


def test_espaces_avertissement(page):
    assert ecrire(page, "   ").warning[0].value == client.REFUS


def test_api_injoignable(monkeypatch):
    monkeypatch.setattr(client, "creer_session",
                        lambda: httpx.Client(base_url="http://127.0.0.1:9", timeout=1))
    page = AppTest.from_file(PAGE, default_timeout=30).run()
    assert page.sidebar.error[0].value == client.INJOIGNABLE
