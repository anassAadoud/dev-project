"""Tests de l'API du TP3, via TestClient : aucun serveur à lancer.

Ignorés tant que models/support.joblib n'existe pas sur le poste (la CI
l'entraîne avant pytest : voir .github/workflows/ci.yml). Les tickets sont
écrits dans un dossier temporaire (variable SUPPORT_TICKETS).
"""
from pathlib import Path

import pytest

MODELE = Path(__file__).resolve().parents[1] / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from fastapi.testclient import TestClient

    from api.main import app

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUPPORT_TICKETS", str(tmp_path_factory.mktemp("tickets") / "tickets.jsonl"))
        with TestClient(app) as c:  # le "with" déclenche lifespan (chargement du modèle et de la base)
            yield c


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["docs"] == "/docs"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "OK"
    assert "TP2" in body["model"]
    assert body["articles"] >= 21  # au moins 3 articles par catégorie


def test_predict_reseau(client):
    r = client.post("/predict", json={"text": "My VPN keeps disconnecting and the network is unstable"})
    assert r.status_code == 200
    body = r.json()
    assert body["label"] == "reseau"
    assert 0 <= body["score"] <= 1
    assert body["priorite"] in {"high", "medium", "low"}


def test_predict_facturation(client):
    r = client.post("/predict", json={"text": "I was charged twice for the subscription this month"})
    assert r.status_code == 200
    assert r.json()["label"] == "facturation"


def test_predict_texte_vide_422(client):
    assert client.post("/predict", json={"text": ""}).status_code == 422
    assert client.post("/predict", json={"text": "   "}).status_code == 422


def test_predict_champ_manquant_422(client):
    assert client.post("/predict", json={}).status_code == 422
    assert client.post("/predict", json={"text": 42}).status_code == 422


def test_assist_propose_une_solution(client):
    r = client.post("/assist", json={"text": "The printer shows offline and nothing prints, no rush"})
    assert r.status_code == 200
    body = r.json()
    assert body["label"] == "materiel"
    assert body["article"]["id"].startswith("KB-HW")
    assert len(body["article"]["etapes"]) >= 3
    assert body["decision"] in {"solution", "escalade"} and body["raison"]


def test_assist_escalade_une_panne(client):
    r = client.post("/assist", json={"text": "The production database server is down, the whole team is blocked"})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "escalade"
    assert body["groupe"]


def test_ticket_cree_puis_relu(client):
    r = client.post("/tickets", json={"text": "Outlook stopped receiving emails", "article_id": "KB-SW-02",
                                      "raison": "non résolu après l'article KB-SW-02"})
    assert r.status_code == 201
    ticket = r.json()
    assert ticket["id"].startswith("TCK-") and ticket["statut"] == "ouvert"
    assert ticket["label"] and ticket["groupe"]  # pré-rempli par l'API
    relu = client.get(f"/tickets/{ticket['id']}")
    assert relu.status_code == 200 and relu.json() == ticket


def test_ticket_inconnu_404(client):
    assert client.get("/tickets/TCK-INCONNU").status_code == 404
