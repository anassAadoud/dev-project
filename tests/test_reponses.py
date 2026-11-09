"""TP5.2, phase 3 bis : la qualité des réponses.

- La base : au moins 8 articles par catégorie, des étapes précises (menus, commandes, chemins), un champ
  escalade_si, une source quand une étape vient d'une documentation officielle.
- La recherche couvre toute la base : si le classifieur se trompe, le bon article apparaît quand même.
- Les questions de diagnostic : 2 ou 3 par catégorie, chaque réponse cite des articles qui existent.
- La conversation : choisir un article suggéré, répondre au diagnostic (tout le bureau -> panne -> ticket
  proposé, jamais créé sans confirmation) ; ni l'un ni l'autre ne compte comme une tentative.
- Les jeux de validation et indépendant portent les articles attendus (articles_ok).
"""
import csv
import json
import re
import sys
from pathlib import Path

import pytest

from api import conversation as cv
from api.conversation import ActionRefusee, avancer, nouvelle
from tests.test_conversation import FauxOutils

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
MODELE = RACINE / "models" / "support.joblib"
avec_modele = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")
CATEGORIES = ["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]
# Une étape vérifiable nomme un menu, un raccourci, une commande, un chemin ou une adresse.
PRECIS = re.compile(r">|Settings|Ctrl\+|Win(dows)?\+|ipconfig|nslookup|https?://|\\\\|\.exe|Task Manager|"
                    r"Credential Manager|portal|Start menu|button|tray|click \w+|press \w+", re.IGNORECASE)


def lire(nom):
    with (RACINE / "data" / nom).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


ARTICLES = lire("base_connaissances.csv")
IDS = {a["id"] for a in ARTICLES}


# --- La base de connaissances ---

@pytest.mark.parametrize("categorie", CATEGORIES)
def test_au_moins_8_articles_par_categorie(categorie):
    assert sum(a["categorie"] == categorie for a in ARTICLES) >= 8


def test_identifiants_uniques():
    assert len(IDS) == len(ARTICLES)


@pytest.mark.parametrize("article", ARTICLES, ids=lambda a: a["id"])
def test_article_precis_et_verifiable(article):
    etapes = [e for e in article["etapes"].split("|") if e.strip()]
    assert len(etapes) >= 3, "au moins 3 étapes"
    assert any(PRECIS.search(e) for e in etapes), "au moins une étape nomme un menu, une commande ou un chemin"
    assert article["escalade_si"].strip(), "le champ escalade_si dit quand appeler un technicien"


def test_les_sources_officielles_sont_citees():
    """Les étapes reprises d'une documentation officielle citent leur source (Microsoft Support, Microsoft Learn)."""
    sources = [a for a in ARTICLES if a.get("source")]
    assert len(sources) >= 15
    assert all(re.match(r"(Microsoft (Support|Learn)|Cisco|Apple|Google) ", a["source"]) for a in sources)


# --- La recherche dans toute la base ---

def test_le_bon_article_apparait_meme_si_la_categorie_est_fausse():
    """Le classifieur dit « réseau », l'incident est un logiciel : l'article Outlook est quand même proposé."""
    from kb import proposer

    ids = [a["id"] for a in proposer("Outlook keeps asking for my password again and again", "reseau")]
    assert "KB-SW-07" in ids
    assert len(ids) <= 3


def test_la_categorie_predite_donne_un_bonus():
    from kb import proposer

    texte = "the second monitor stays black"
    assert proposer(texte, "materiel")[0]["categorie"] == "materiel"


def test_exclus_et_preferes():
    from kb import proposer

    texte = "VPN keeps disconnecting from home"
    assert proposer(texte, "reseau")[0]["id"] == "KB-NET-01"
    assert "KB-NET-01" not in [a["id"] for a in proposer(texte, "reseau", exclus=["KB-NET-01"])]
    assert proposer(texte, "reseau", preferes=["KB-NET-08"])[0]["id"] == "KB-NET-08"


def test_message_vague_sans_article():
    from kb import proposer

    assert proposer("It's not working again", None) == []


# --- Les questions de diagnostic ---

def test_deux_ou_trois_questions_par_categorie():
    from api.model import charger_questions

    questions = charger_questions()
    assert set(questions) == set(CATEGORIES)
    for categorie, liste in questions.items():
        assert 2 <= len(liste) <= 3, categorie
        assert all(len(q["options"]) >= 2 for q in liste), categorie


def test_un_article_inconnu_est_refuse(tmp_path):
    from api.model import charger_questions

    faux = {"reseau": [{"id": "q", "question": "?", "options": [{"id": "a", "label": "A",
                                                                  "effet": {"articles": ["KB-NET-99"]}}]}]}
    chemin = tmp_path / "questions.json"
    chemin.write_text(json.dumps(faux), encoding="utf-8")
    with pytest.raises(ValueError, match="KB-NET-99"):
        charger_questions(chemin)


def test_tout_le_bureau_reseau_devient_une_panne():
    from api.model import charger_questions

    portee = charger_questions()["reseau"][0]
    tous = next(o for o in portee["options"] if o["id"] == "tous")
    assert tous["effet"] == {"categorie": "panne_service"}


# --- La conversation, avec les faux outils de test_conversation.py ---

@pytest.fixture
def outils():
    return FauxOutils()


def test_la_question_de_diagnostic_accompagne_l_article(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="My VPN keeps disconnecting")
    assert conv["phase"] == "solution" and conv["question"]["id"] == "portee"
    assert "diagnostic" in cv.actions_possibles(conv)


def test_tout_le_bureau_propose_un_ticket_sans_le_creer(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="My VPN keeps disconnecting")
    conv = avancer(conv, "diagnostic", outils, question_id="portee", option_id="tous")
    assert conv["categorie"] == "panne_service"
    assert (conv["phase"], conv["code"]) == ("proposition_ticket", "critique")
    assert conv["ticket_id"] is None and outils.tickets == []
    assert conv["tentatives"] == 0


def test_la_reponse_fait_passer_un_article_devant(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="My VPN keeps disconnecting")
    assert conv["article"]["id"] == "NET-1"
    conv = avancer(conv, "diagnostic", outils, question_id="portee", option_id="moi")
    assert conv["article"]["id"] == "NET-2" and conv["tentatives"] == 0
    assert conv["question"] is None  # la seule question de la catégorie a été posée


def test_mauvaise_question_ou_reponse_refusee(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="My VPN keeps disconnecting")
    with pytest.raises(ActionRefusee):
        avancer(conv, "diagnostic", outils, question_id="autre", option_id="moi")
    with pytest.raises(ActionRefusee):
        avancer(conv, "diagnostic", outils, question_id="portee", option_id="peut-etre")


def test_choisir_un_article_suggere(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="My VPN keeps disconnecting")
    assert [a["id"] for a in conv["suggestions"]] == ["NET-2", "HW-1"]
    conv = avancer(conv, "choisir_article", outils, article_id="HW-1")
    assert conv["article"]["id"] == "HW-1" and conv["categorie"] == "materiel"
    assert conv["phase"] == "solution" and conv["tentatives"] == 0


def test_un_article_non_suggere_est_refuse(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="My VPN keeps disconnecting")
    with pytest.raises(ActionRefusee):
        avancer(conv, "choisir_article", outils, article_id="SEC-1-INVENTE")


def test_le_modele_hesite_mais_les_articles_sont_montres(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="Something odd happens on my computer")
    assert conv["phase"] == "precision" and conv["article"] is None
    assert len(conv["suggestions"]) == 3
    assert "choisir_article" in cv.actions_possibles(conv)


def test_choisir_un_article_critique_propose_le_ticket(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="Something odd happens on my computer")
    conv["suggestions"] = [FauxOutils.BASE["securite"][0]]  # la base suggère un article de sécurité
    conv = avancer(conv, "choisir_article", outils, article_id="SEC-1")
    assert (conv["phase"], conv["code"]) == ("proposition_ticket", "critique")
    assert conv["ticket_id"] is None


def test_un_message_apres_la_proposition_critique_ne_la_refait_pas(outils):
    """Règle du TP5.1 : le cas critique est proposé une fois ; un message ensuite donne une solution."""
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="I received a phishing email")
    assert conv["code"] == "critique"
    conv = avancer(conv, "message", outils, texte="the phishing email had a link")
    assert conv["phase"] == "solution"


def test_une_conversation_d_avant_le_tp52_se_relit(outils):
    conv = avancer(nouvelle("CNV-T"), "message", outils, texte="My VPN keeps disconnecting")
    for cle in ["suggestions", "preferes", "diagnostics", "question"]:
        conv.pop(cle)  # type: ignore[misc]
    conv = avancer(conv, "resolu", outils)
    assert conv["phase"] == "resolu"


# --- Les jeux étiquetés ---

@pytest.mark.parametrize("nom", ["jeu_validation.csv", "jeu_independant.csv"])
def test_articles_attendus(nom):
    for ligne in lire(nom):
        ok = ligne["articles_ok"].split()
        if ligne["attendu"] == "hors_sujet":
            assert not ok, ligne["text"]
        else:
            assert ok and set(ok) <= IDS, ligne["text"]


# --- Avec le vrai modèle ---

@avec_modele
def test_top3_des_articles_sur_la_validation():
    """Mesuré au TP5.2 : top-1 75 %, top-3 86 % (avant : 52 % et 58 %). Le plancher laisse la place des graines."""
    from evaluer_articles import mesurer

    r = mesurer("validation", "toute+")
    assert r["top1"] >= 0.65 and r["top3"] >= 0.78, r


@pytest.fixture
def client(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setenv("SUPPORT_TICKETS", str(tmp_path / "tickets.jsonl"))
    monkeypatch.delenv("SUPPORT_LLM", raising=False)
    with TestClient(app) as c:
        yield c


@avec_modele
def test_assist_renvoie_les_trois_articles(client):
    r = client.post("/assist", json={"text": "Outlook keeps asking for my password"}).json()
    assert 1 <= len(r["articles"]) <= 3
    assert r["article"]["id"] == r["articles"][0]["id"]


@avec_modele
def test_chat_diagnostic_tout_le_bureau(client):
    r = client.post("/chat", json={"text": "The Wi-Fi drops every few minutes on my laptop"}).json()
    assert r["phase"] == "solution" and r["question"]["id"] == "reseau_portee"
    r = client.post("/chat", json={"conversation_id": r["conversation_id"], "action": "diagnostic",
                                   "question_id": "reseau_portee", "option_id": "tous"}).json()
    assert (r["phase"], r["code"], r["categorie"]) == ("proposition_ticket", "critique", "panne_service")
    assert r["ticket"] is None


@avec_modele
@pytest.mark.parametrize("corps", [{"action": "choisir_article"}, {"action": "diagnostic", "question_id": "x"}])
def test_chat_champs_obligatoires(client, corps):
    r = client.post("/chat", json={"text": "printer offline"}).json()
    assert client.post("/chat", json={"conversation_id": r["conversation_id"], **corps}).status_code == 422
