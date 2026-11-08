"""Tests de la conversation par l'API (TP5.1) : /chat, le suivi des tickets, les avis et les statistiques.

L'API tourne en mémoire (TestClient) sur le modèle de démonstration ; les tickets, les
conversations et les avis sont écrits dans un dossier temporaire (variable SUPPORT_TICKETS).
"""
from pathlib import Path

import pytest

MODELE = Path(__file__).resolve().parents[1] / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")

VPN = "My VPN keeps disconnecting every 10 minutes when I work from home"


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Une API neuve par test : chaque test a ses propres fichiers de tickets et de conversations."""
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setenv("SUPPORT_TICKETS", str(tmp_path / "tickets.jsonl"))
    monkeypatch.delenv("SUPPORT_LLM", raising=False)
    with TestClient(app) as c:
        yield c


def dire(client, conversation_id=None, **champs):
    r = client.post("/chat", json={"conversation_id": conversation_id, **champs})
    assert r.status_code == 200, r.text
    return r.json()


def jusqu_au_ticket(client):
    """L'utilisateur répond « pas résolu » à chaque article et précise quand on le lui demande,
    jusqu'à ce que l'agent propose le ticket (deux tentatives) ; puis il confirme."""
    r = dire(client, text=VPN)
    for _ in range(4):
        if r["phase"] == "proposition_ticket":
            break
        assert r["ticket"] is None
        if r["phase"] == "solution":
            r = dire(client, r["conversation_id"], action="pas_resolu", etapes_faites=r["article"]["etapes"][:2])
        else:
            r = dire(client, r["conversation_id"], text="The VPN client still drops the connection")
    assert (r["phase"], r["code"], r["tentatives"]) == ("proposition_ticket", "deux_essais", 2) and r["ticket"] is None
    return dire(client, r["conversation_id"], action="confirmer_ticket")


def test_premier_message_une_solution_pas_de_ticket(client):
    r = dire(client, text=VPN)
    assert r["conversation_id"].startswith("CNV-") and r["tour"] == 1
    assert (r["phase"], r["code"], r["label"]) == ("solution", "solution", "reseau")
    assert r["article"]["id"].startswith("KB-NET") and len(r["article"]["etapes"]) >= 3
    assert {"resolu", "pas_resolu", "demander_ticket"} <= set(r["choix"])
    assert r["ticket"] is None and client.get("/tickets").json() == []


def test_resolu_ferme_sans_ticket(client):
    r = dire(client, text=VPN)
    r = dire(client, r["conversation_id"], action="resolu")
    assert (r["phase"], r["code"], r["choix"]) == ("resolu", "resolu", [])
    assert client.get("/tickets").json() == []


def test_deux_essais_puis_ticket_pre_rempli(client):
    r = jusqu_au_ticket(client)
    ticket = r["ticket"]
    assert (r["phase"], r["code"]) == ("ticket", "ticket_cree")
    assert ticket["conversation_id"] == r["conversation_id"] and ticket["label"] == "reseau"
    assert ticket["groupe"] == "Network" and ticket["statut"] == "ouvert"
    assert ticket["resume"].startswith("My VPN keeps disconnecting")
    assert ticket["essais"] and ticket["essais"][0]["etapes_faites"]  # les articles essayés, les étapes cochées
    assert len({e["article_id"] for e in ticket["essais"]}) == len(ticket["essais"])  # jamais deux fois le même
    assert "2 tentatives" in ticket["raison"]
    assert client.get(f"/tickets/{ticket['id']}").json() == ticket


def test_un_seul_ticket_par_conversation(client):
    r = jusqu_au_ticket(client)
    deuxieme = client.post("/chat", json={"conversation_id": r["conversation_id"], "action": "confirmer_ticket"})
    assert deuxieme.status_code == 409 and "un seul ticket" in deuxieme.json()["detail"]
    direct = client.post("/tickets", json={"text": VPN, "conversation_id": r["conversation_id"]})
    assert direct.status_code == 409
    assert len(client.get("/tickets").json()) == 1


def test_le_modele_hesite_boutons_de_categories(client):
    r = dire(client, text="xqzvb wlkptr grombu")
    assert (r["phase"], r["code"], r["label"]) == ("precision", "reformuler", "INDETERMINE")
    assert sorted(r["categories"]) == sorted(["securite", "reseau", "materiel", "compte_acces", "facturation",
                                              "logiciel", "panne_service"])
    r = dire(client, r["conversation_id"], action="categorie", categorie="materiel")
    assert r["categorie"] == "materiel" and r["phase"] in {"solution", "precision"}
    assert client.get("/tickets").json() == []


def test_critique_propose_le_ticket_mais_attend_la_confirmation(client):
    r = dire(client, text="A ransomware message appeared and my files are encrypted")
    assert (r["phase"], r["code"], r["categorie"]) == ("proposition_ticket", "critique", "securite")
    assert r["article"] is not None and client.get("/tickets").json() == []
    r = dire(client, r["conversation_id"], action="confirmer_ticket")
    assert r["ticket"]["groupe"] == "Security (SOC)"


def test_demande_explicite(client):
    r = dire(client, text="Please open a ticket, Outlook stopped receiving emails")
    assert (r["phase"], r["code"]) == ("proposition_ticket", "demande") and r["ticket"] is None


@pytest.mark.parametrize("corps", [
    {"action": "resolu"},                                   # sans conversation
    {"action": "message"},                                  # sans texte
    {"action": "message", "text": "   "},                   # que des blancs
    {"conversation_id": "CNV-1", "action": "categorie"},    # sans catégorie
    {"text": "x" * 2001},                                   # trop long
    {"text": VPN, "action": "danser"},                      # action inconnue
])
def test_requetes_refusees_422(client, corps):
    assert client.post("/chat", json=corps).status_code == 422


def test_conversation_inconnue_404(client):
    r = client.post("/chat", json={"conversation_id": "CNV-INCONNUE", "action": "resolu"})
    assert r.status_code == 404 and r.json() == {"detail": "Conversation introuvable"}


def test_action_hors_de_propos_409(client):
    r = dire(client, text=VPN)
    refus = client.post("/chat", json={"conversation_id": r["conversation_id"], "action": "confirmer_ticket"})
    assert refus.status_code == 409


def test_panne_du_chat_500(client, monkeypatch):
    from api.model import SupportClassifier

    def en_panne(self, *args, **kwargs):
        raise RuntimeError("panne interne")

    monkeypatch.setattr(SupportClassifier, "discuter", en_panne)
    r = client.post("/chat", json={"text": VPN})
    assert r.status_code == 500 and "panne interne" not in r.text


def test_la_conversation_survit_au_redemarrage(client):
    from fastapi.testclient import TestClient

    from api.main import app

    r = dire(client, text=VPN)
    with TestClient(app) as autre:  # une nouvelle API relit la conversation dans le fichier
        suite = autre.post("/chat", json={"conversation_id": r["conversation_id"], "action": "resolu"})
    assert suite.status_code == 200 and suite.json()["phase"] == "resolu"


def test_suivi_du_statut(client):
    ticket = jusqu_au_ticket(client)["ticket"]
    r = client.patch(f"/tickets/{ticket['id']}", json={"statut": "en_cours", "commentaire": "taken by Sam"})
    assert r.status_code == 200 and r.json()["statut"] == "en_cours"
    r = client.patch(f"/tickets/{ticket['id']}", json={"statut": "resolu", "resolution": "VPN profile reinstalled"})
    suivi = client.get(f"/tickets/{ticket['id']}").json()
    assert suivi["statut"] == "resolu" and suivi["resolution"] == "VPN profile reinstalled"
    assert [e["statut"] for e in suivi["historique"]] == ["ouvert", "en_cours", "resolu"]
    assert suivi["historique"][1]["commentaire"] == "taken by Sam"
    assert len(client.get("/tickets").json()) == 1  # une version actuelle par ticket


def test_suivi_refuse(client):
    assert client.patch("/tickets/TCK-INCONNU", json={"statut": "resolu"}).status_code == 404
    ticket = jusqu_au_ticket(client)["ticket"]
    assert client.patch(f"/tickets/{ticket['id']}", json={"statut": "perdu"}).status_code == 422


def test_ticket_passe_le_plus_semblable(client):
    ticket = jusqu_au_ticket(client)["ticket"]
    client.patch(f"/tickets/{ticket['id']}", json={"statut": "resolu", "resolution": "VPN profile reinstalled"})
    r = dire(client, text="My VPN keeps disconnecting when I work from home")
    assert r["ticket_semblable"]["id"] == ticket["id"]
    assert r["ticket_semblable"]["resolution"] == "VPN profile reinstalled"
    assert r["ticket_semblable"]["source"] == "agent tickets"


def test_avis_sur_une_reponse(client):
    r = dire(client, text=VPN)
    avis = client.post("/feedback", json={"conversation_id": r["conversation_id"], "tour": 1, "utile": True})
    assert avis.status_code == 201 and avis.json()["code"] == "solution" and avis.json()["id"].startswith("AVS-")
    assert client.post("/feedback", json={"conversation_id": "CNV-X", "tour": 1, "utile": True}).status_code == 404
    assert client.post("/feedback", json={"conversation_id": r["conversation_id"], "tour": 9,
                                          "utile": False}).status_code == 404


def test_statistiques(client):
    vide = client.get("/stats").json()
    assert vide["conversations"] == 0 and vide["taux_resolution_sans_ticket"] is None
    r = dire(client, text=VPN)
    dire(client, r["conversation_id"], action="resolu")
    client.post("/feedback", json={"conversation_id": r["conversation_id"], "tour": 1, "utile": True})
    jusqu_au_ticket(client)
    dire(client, text="xqzvb wlkptr grombu")  # en cours
    stats = client.get("/stats").json()
    assert (stats["conversations"], stats["resolues_sans_ticket"], stats["avec_ticket"], stats["en_cours"]) == (3, 1, 1, 1)
    assert stats["taux_resolution_sans_ticket"] == 0.5
    assert stats["categories"]["reseau"] == 2 and stats["categories"]["INDETERMINE"] == 1
    assert stats["tickets_par_statut"] == {"ouvert": 1}
    assert (stats["avis_utiles"], stats["avis_pas_utiles"]) == (1, 0)
    assert stats["tentatives_moyennes"] == pytest.approx(0.67)


def test_sante_llm_desactive_par_defaut(client):
    assert client.get("/health").json()["llm"] == "off"
    assert dire(client, text=VPN)["reformulation"] is None


def test_reformulation_ollama_simulee(client, monkeypatch):
    """L'option LLM, sans Ollama : sa réponse est simulée, les tests n'en dépendent pas."""
    import httpx

    from api import llm

    appels = []

    def faux_post(url, json, timeout):
        appels.append(json)
        return httpx.Response(200, json={"response": "Restart the VPN client, then reconnect."},
                              request=httpx.Request("POST", url))

    monkeypatch.setenv("SUPPORT_LLM", "ollama")
    monkeypatch.setattr(llm.httpx, "post", faux_post)
    r = dire(client, text=VPN)
    assert r["reformulation"] == "Restart the VPN client, then reconnect."
    assert r["article"]["titre"] in appels[0]["prompt"] and client.get("/health").json()["llm"].startswith("ollama")
