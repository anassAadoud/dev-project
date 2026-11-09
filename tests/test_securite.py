"""Sécurité et fiabilité de l'API (TP5.2, phase 6).

Limite de taille des requêtes, en-têtes de sécurité, refus et pannes sans fuite d'information, identifiants
mal formés, CORS restreint, stockage abîmé, fichiers absents au démarrage.
"""
import json
from pathlib import Path

import pytest

MODELE = Path(__file__).resolve().parents[1] / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")
SECRET = "mon-mot-de-passe-Secret123"


@pytest.fixture
def client(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setenv("SUPPORT_TICKETS", str(tmp_path / "tickets.jsonl"))
    monkeypatch.delenv("SUPPORT_LLM", raising=False)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# --- Taille des requêtes ---

def test_corps_trop_gros_refuse(client):
    r = client.post("/predict", content=b'{"text": "' + b"a" * 140_000 + b'"}',
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_corps_par_morceaux_trop_gros_refuse(client):
    """Sans Content-Length (envoi par morceaux), la limite s'applique aussi."""
    def morceaux():
        yield b'{"text": "'
        for _ in range(40):
            yield b"a" * 4096
        yield b'"}'

    r = client.post("/predict", content=morceaux(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_le_plus_gros_message_legitime_passe(client):
    """2 000 caractères et 20 étapes cochées de 500 caractères : le plus gros /chat possible tient dans la limite."""
    r = client.post("/chat", json={"text": "printer offline " + "a" * 1980})
    assert r.status_code == 200
    conv = r.json()["conversation_id"]
    r = client.post("/chat", json={"conversation_id": conv, "action": "message", "text": "é" * 2000,
                                   "etapes_faites": ["é" * 500] * 20})
    assert r.status_code == 200


@pytest.mark.parametrize("corps", [
    {"text": "printer offline", "etapes_faites": ["a" * 501]},
    {"text": "printer offline", "conversation_id": "C" * 41},
])
def test_champs_limites(client, corps):
    assert client.post("/chat", json=corps).status_code == 422


def test_avis_tour_absurde_refuse(client):
    assert client.post("/feedback", json={"conversation_id": "CNV-1234ABCD", "tour": 10**9, "utile": True}).status_code == 422


# --- Pas de fuite d'information ---

def test_un_refus_ne_renvoie_pas_le_texte_recu(client):
    r = client.post("/predict", json={"text": SECRET + " " * 2000})
    assert r.status_code == 422
    assert SECRET not in r.text
    assert all(set(e) == {"loc", "msg", "type"} for e in r.json()["detail"])


def test_une_panne_imprevue_ne_montre_ni_trace_ni_chemin(client, monkeypatch):
    from api import tickets

    def panne():
        raise RuntimeError(f"C:/secret/chemin/tickets.jsonl {SECRET}")

    monkeypatch.setattr(tickets, "lister", panne)
    r = client.get("/tickets")
    assert r.status_code == 500 and r.json() == {"detail": "Erreur interne du serveur"}
    assert SECRET not in r.text and "Traceback" not in r.text


def test_en_tetes_de_securite(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["cache-control"] == "no-store"


# --- Identifiants ---

@pytest.mark.parametrize("identifiant", ["..%2F..%2Fetc%2Fpasswd", "TCK-" + "A" * 500, "tck-1234abcd", "TCK-12"])
def test_identifiant_de_ticket_mal_forme(client, monkeypatch, identifiant):
    """Un identifiant mal formé répond 404 sans que le stockage soit lu."""
    from api import stockage

    def interdit(*args, **kwargs):
        raise AssertionError("le stockage ne doit pas être lu")

    monkeypatch.setattr(stockage, "lire", interdit)
    assert client.get(f"/tickets/{identifiant}").status_code == 404
    assert client.patch(f"/tickets/{identifiant}", json={"statut": "resolu"}).status_code == 404


@pytest.mark.parametrize("identifiant", ["CNV-INCONNUE", "../conversations", "CNV-1234abcd"])
def test_identifiant_de_conversation_mal_forme(client, identifiant):
    assert client.post("/chat", json={"conversation_id": identifiant, "action": "resolu"}).status_code == 404
    assert client.post("/feedback", json={"conversation_id": identifiant, "tour": 1, "utile": True}).status_code == 404
    r = client.post("/tickets", json={"text": "printer offline", "conversation_id": identifiant})
    assert r.status_code == 404


def test_les_identifiants_crees_ont_le_bon_format(client):
    from api import securite

    r = client.post("/chat", json={"text": "I clicked a phishing link and typed my password"}).json()
    assert securite.conversation_valide(r["conversation_id"])
    ticket = client.post("/tickets", json={"text": "printer offline"}).json()
    assert securite.ticket_valide(ticket["id"])


# --- CORS ---

def test_cors_page_locale_autorisee(client):
    r = client.options("/predict", headers={"Origin": "http://localhost:8501", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:8501"


def test_cors_autre_site_refuse(client):
    r = client.options("/predict", headers={"Origin": "https://pirate.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers


def test_origines_configurables(monkeypatch):
    from api import securite

    monkeypatch.setenv("SUPPORT_ORIGINES", "https://support.company.example, https://intranet.company.example")
    assert securite.origines() == ["https://support.company.example", "https://intranet.company.example"]


# --- Stockage abîmé ---

def test_une_ligne_abimee_n_empeche_pas_de_lire_les_autres(client, tmp_path):
    ticket = client.post("/tickets", json={"text": "printer offline"}).json()
    with (tmp_path / "tickets.jsonl").open("a", encoding="utf-8") as f:
        f.write('{"id": "TCK-AAAAAAAA", "statut": \n')  # une écriture coupée
        f.write("pas du json\n")
        f.write(json.dumps({"sans": "identifiant"}) + "\n")
    r = client.get("/tickets")
    assert r.status_code == 200 and [t["id"] for t in r.json()] == [ticket["id"]]
    assert client.get(f"/tickets/{ticket['id']}").status_code == 200


# --- Fichiers absents au démarrage ---

def test_refus_de_demarrer_sans_questions_de_diagnostic(monkeypatch, tmp_path):
    """Comme le modèle et la base : un fichier de l'agent manque, l'API refuse de démarrer (message clair)."""
    from fastapi.testclient import TestClient

    from api import model
    from api.main import app

    monkeypatch.setattr(model, "QUESTIONS", tmp_path / "absent.json")
    monkeypatch.setattr(model.charger_questions, "__defaults__", (tmp_path / "absent.json",))
    with pytest.raises(FileNotFoundError, match="absent.json"), TestClient(app):
        pass
