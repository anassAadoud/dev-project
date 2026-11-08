"""Tests du client de l'API (TP5) : l'API tourne en mémoire, aucun serveur à lancer."""
from pathlib import Path

import httpx
import pytest

from ui import client

MODELE = Path(__file__).resolve().parents[1] / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    from fastapi.testclient import TestClient

    from api.main import app

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUPPORT_TICKETS", str(tmp_path_factory.mktemp("tickets") / "tickets.jsonl"))
        with TestClient(app) as c:  # un client httpx branché directement sur l'API
            yield c


def test_sante_api_prete(session):
    etat = client.sante(session)
    assert etat.ok and "TP2" in etat.message and "articles" in etat.message


def test_incident_reseau(session):
    r = client.predire(session, "My VPN keeps disconnecting every 10 minutes when I work from home")
    assert r.ok and r.label == "reseau" and r.score is not None


def test_assistance_propose_les_etapes(session):
    r = client.assister(session, "The printer on the second floor shows offline and nothing prints, no rush")
    assert r.ok and r.decision == "solution" and r.motif == "solution"
    assert r.article is not None and len(r.article["etapes"]) >= 3
    assert r.message == client.MOTIFS["solution"]


def test_texte_inconnu_part_au_tri(session):
    r = client.assister(session, "xqzvb wlkptr grombu")
    assert r.ok and r.label == "INDETERMINE" and r.decision == "escalade" and r.groupe == "Triage (L1)"
    assert client.VERDICTS[r.label].startswith("I don't know")


def test_ticket_pre_rempli_avec_l_article_essaye(session):
    aide = client.assister(session, "Outlook stopped receiving emails since this morning")
    ticket = client.creer_ticket(session, "Outlook stopped receiving emails since this morning", aide,
                                 raison="not solved")
    assert ticket.ok and ticket.ticket is not None
    assert ticket.ticket["label"] == aide.label and ticket.ticket["article_id"] == (aide.article or {}).get("id")
    assert ticket.ticket["id"] in ticket.message


def test_espaces_refuses(session):
    r = client.assister(session, "   ")
    assert not r.ok and r.message == client.REFUS


def test_modele_non_charge(session, monkeypatch):
    from api.main import app

    monkeypatch.setattr(app.state, "classifier", None)
    assert client.assister(session, "My VPN keeps disconnecting").message == client.SANS_MODELE
    assert client.sante(session).message == client.SANS_MODELE


def test_api_injoignable():
    with httpx.Client(base_url="http://127.0.0.1:9", timeout=1) as sans_serveur:
        assert client.assister(sans_serveur, "My VPN keeps disconnecting").message == client.INJOIGNABLE
        assert client.creer_ticket(sans_serveur, "My VPN keeps disconnecting").message == client.INJOIGNABLE


def test_lot_et_resume(session):
    reponses = client.assister_lot(session, ["My VPN keeps disconnecting every 10 minutes when I work from home",
                                             "xqzvb wlkptr grombu", "   "])
    assert client.resumer(reponses) == {"INDETERMINE": 1, "REFUSED OR ERROR": 1, "reseau": 1}
    assert client.a_escalader(reponses) == 1


# --- TP5.1 : la conversation, le suivi, les avis, les statistiques ---

def test_conversation_jusqu_a_resolu(session):
    r = client.discuter(session, texte="My VPN keeps disconnecting every 10 minutes when I work from home")
    assert r.ok and r.phase == "solution" and r.code == "solution" and r.message == client.REPLIQUES["solution"]
    assert r.conversation_id and r.tour == 1 and "resolu" in r.choix and r.article
    fin = client.discuter(session, "resolu", r.conversation_id)
    assert fin.ok and fin.phase == "resolu" and fin.choix == []


def test_conversation_jusqu_au_ticket_puis_suivi(session):
    r = client.discuter(session, texte="Please open a ticket, my VPN keeps disconnecting")
    assert r.code == "demande" and r.ticket is None
    r = client.discuter(session, "confirmer_ticket", r.conversation_id)
    assert r.ok and r.ticket and r.groupe == "Network"
    suivi = client.suivre_ticket(session, r.ticket["id"].lower())  # l'identifiant tapé en minuscules
    assert suivi.ok and suivi.message.endswith("Open")
    maj = client.mettre_a_jour_ticket(session, r.ticket["id"], "resolu", "done", "VPN profile reinstalled")
    assert maj.ok and "Resolved" in maj.message
    assert client.discuter(session, "confirmer_ticket", r.conversation_id).message == client.HORS_DE_PROPOS


def test_avis_et_statistiques(session):
    r = client.discuter(session, texte="Outlook stopped receiving emails since this morning")
    assert client.donner_avis(session, r.conversation_id, 1, True).ok
    assert client.donner_avis(session, "CNV-INCONNUE", 1, True).message == client.INTROUVABLE
    stats = client.statistiques(session)
    assert stats.ok and stats.corps["avis_utiles"] >= 1 and stats.corps["conversations"] >= 1


def test_suivi_introuvable(session):
    assert client.suivre_ticket(session, "TCK-INCONNU").message == client.INTROUVABLE
    assert client.mettre_a_jour_ticket(session, "TCK-INCONNU", "resolu").message == client.INTROUVABLE


def test_refus_et_api_injoignable_tp5_1(session):
    assert client.discuter(session, texte="   ").message == client.REFUS
    with httpx.Client(base_url="http://127.0.0.1:9", timeout=1) as sans_serveur:
        for reponse in [client.discuter(sans_serveur, texte="VPN"), client.donner_avis(sans_serveur, "C", 1, True),
                        client.suivre_ticket(sans_serveur, "TCK-1"), client.statistiques(sans_serveur),
                        client.mettre_a_jour_ticket(sans_serveur, "TCK-1", "resolu")]:
            assert reponse.message == client.INJOIGNABLE


def test_conversation_sans_modele(session, monkeypatch):
    from api.main import app

    monkeypatch.setattr(app.state, "classifier", None)
    assert client.discuter(session, texte="VPN").message == client.SANS_MODELE


def test_chaque_code_a_sa_replique():
    from typing import get_args

    from api.schemas import Code, Statut

    assert set(client.REPLIQUES) == set(get_args(Code)) and set(client.STATUTS) == set(get_args(Statut))
