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


@pytest.mark.parametrize("similarite, attendu", [(0.50, ("compte_acces", "base")), (0.10, ("INDETERMINE", "aucune"))])
def test_second_avis_de_la_base(client, monkeypatch, similarite, attendu):
    """TP5.1 : le modèle hésite (confiance sous 0,60) ; la base tranche si un article ressemble assez au texte.
    TP5.2 : le modèle est simulé, pour tester la règle et non le modèle du moment."""
    import api.model

    monkeypatch.setattr(api.model, "_predict", lambda t: {"label": "logiciel", "score": 0.40, "priorite": "medium",
                                                          "connus": 1.0})
    monkeypatch.setattr(api.model, "article_le_plus_proche", lambda t: ("compte_acces", similarite))
    body = client.post("/predict", json={"text": "my account is locked after too many attempts"}).json()
    assert (body["label"], body["source"]) == attendu


@pytest.mark.parametrize("texte", ["It does not work", "it is broken, please help", "not working again!!"])
def test_message_trop_vague_n_est_jamais_tranche(client, texte):
    """TP5.2 : sans aucun mot qui décrive l'incident, l'agent ne devine pas."""
    assert client.post("/predict", json={"text": texte}).json()["label"] == "INDETERMINE"


@pytest.mark.parametrize("texte", ["phishing??", "virus??", "printer offline"])
def test_un_seul_mot_utile_suffit(client, texte):
    assert client.post("/predict", json={"text": texte}).json()["label"] != "INDETERMINE"


@pytest.mark.parametrize("texte", ["Mon VPN ne se connecte plus depuis ce matin", "xqzvb wlkptr grombu"])
def test_mots_inconnus_jamais_tranches_par_la_base(client, texte):
    """Une autre langue ou du charabia va au tri, même si un mot (VPN) ressemble à un article."""
    body = client.post("/predict", json={"text": texte}).json()
    assert (body["label"], body["source"]) == ("INDETERMINE", "aucune")


@pytest.mark.parametrize("texte", ["Tell me a joke", "What is the meaning of life right now?",
                                   "Our coffee machine leaks water on the floor"])
def test_hors_sujet_va_au_tri(client, texte):
    """TP5.1 : les mots vides ne comptent plus comme des mots connus."""
    assert client.post("/predict", json={"text": texte}).json()["label"] == "INDETERMINE"


def test_source_du_modele(client):
    body = client.post("/predict", json={"text": "My VPN keeps disconnecting and the network is unstable"}).json()
    assert body["source"] == "modele"


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
