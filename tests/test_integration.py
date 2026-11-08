"""Tests d'intégration : l'API telle qu'elle tourne vraiment (TP4, étape D).

Les tests du TP3 vérifient des réponses ; ceux-ci vérifient le démarrage de l'API
et son comportement quand le modèle ou la base manque, ou quand le modèle tombe en panne.
"""
from pathlib import Path

import pytest

MODELE = Path(__file__).resolve().parents[1] / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Une API démarrée pour de bon, le temps d'un test ; tickets dans un dossier temporaire."""
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setenv("SUPPORT_TICKETS", str(tmp_path / "tickets.jsonl"))
    with TestClient(app) as c:
        yield c


def test_demarrage_reel_charge_le_modele_et_la_base():
    """D.1 : un client ouvert par « with » exécute le lifespan."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        reponse = client.get("/health")
    assert reponse.status_code == 200
    assert "TP2" in reponse.json()["model"] and reponse.json()["articles"] >= 21


def test_refus_de_demarrer_sans_modele(monkeypatch, tmp_path):
    """D.2 : modèle introuvable, l'API refuse de démarrer plutôt que de répondre faux."""
    from fastapi.testclient import TestClient

    from api.main import app
    import predict  # le module que l'API utilise vraiment (src/ est sur le chemin depuis api.model)

    monkeypatch.setattr(predict, "MODELE", tmp_path / "absent.joblib")
    predict.charger_modele.cache_clear()  # sinon le modèle déjà chargé resterait en mémoire
    try:
        with pytest.raises(FileNotFoundError), TestClient(app):
            pass
    finally:
        predict.charger_modele.cache_clear()  # le prochain test recharge le vrai modèle


def test_refus_de_demarrer_sans_base(monkeypatch, tmp_path):
    """La base de connaissances suit la même règle que le modèle."""
    from fastapi.testclient import TestClient

    import kb
    from api.main import app

    monkeypatch.setattr(kb, "BASE", tmp_path / "absente.csv")
    kb.charger_base.cache_clear()
    try:
        with pytest.raises(FileNotFoundError), TestClient(app):
            pass
    finally:
        kb.charger_base.cache_clear()


def test_modele_retire_repond_503(client, monkeypatch):
    """D.3 : l'API tourne mais n'a plus de modèle : 503 partout, même message."""
    from api.main import app

    monkeypatch.setattr(app.state, "classifier", None)
    assert client.get("/health").status_code == 503
    for route in ["/predict", "/assist", "/tickets"]:
        reponse = client.post(route, json={"text": "My VPN keeps disconnecting"})
        assert reponse.status_code == 503, route
        assert reponse.json() == {"detail": "Modèle non chargé"}


@pytest.mark.parametrize(
    "panne",
    [RuntimeError("panne du modèle"), ValueError("bug interne")],
    ids=["RuntimeError", "ValueError"],
)
@pytest.mark.parametrize("route", ["/predict", "/assist", "/tickets"])
def test_panne_du_modele_repond_500(client, monkeypatch, panne, route):
    """D.4 : toute panne du modèle donne 500, sans jamais montrer le message interne."""
    from api.model import SupportClassifier

    def en_panne(self, text):
        raise panne

    monkeypatch.setattr(SupportClassifier, "predict", en_panne)
    monkeypatch.setattr(SupportClassifier, "assist", en_panne)
    reponse = client.post(route, json={"text": "My VPN keeps disconnecting"})
    assert reponse.status_code == 500
    assert reponse.json() == {"detail": "Erreur interne du serveur"}
    assert str(panne) not in reponse.text


def test_ticket_d_un_incident_indetermine_va_au_tri(client):
    """Un ticket créé pour un incident incertain part au groupe de tri N1."""
    reponse = client.post("/tickets", json={"text": "xqzvb wlkptr grombu"})
    assert reponse.status_code == 201
    assert reponse.json()["label"] == "INDETERMINE" and reponse.json()["groupe"] == "Tri N1"


def test_lire_un_ticket_sans_fichier_repond_404(client):
    """Avant le premier ticket, le fichier n'existe pas : la lecture répond 404, sans planter."""
    assert client.get("/tickets/TCK-00000000").status_code == 404
