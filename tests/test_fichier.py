"""L'onglet « A file of tickets » (TP5.2, phase 5) : lecture tolérante, résultats, cas critiques confirmés."""
from pathlib import Path

import pandas as pd
import pytest

from ui import client, fichier

MODELE = Path(__file__).resolve().parents[1] / "models" / "support.joblib"
avec_modele = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")


# --- Lecture ---

def test_csv_simple():
    lecture = fichier.lire(b"text\nVPN keeps disconnecting\nprinter offline\n")
    assert lecture.erreur is None and list(lecture.tickets["text"]) == ["VPN keeps disconnecting", "printer offline"]


def test_excel_point_virgule_bom_et_casse():
    """Un CSV enregistré par Excel en français : BOM, point-virgule, colonne « Text »."""
    octets = "id;Text\n1;Mot de passe expiré, impossible de me connecter\n2;printer offline\n".encode("utf-8-sig")
    lecture = fichier.lire(octets)
    assert lecture.erreur is None and lecture.colonne == "Text"
    assert lecture.tickets.loc[0, "Text"].startswith("Mot de passe expiré")


def test_latin_1():
    lecture = fichier.lire("text\nécran cassé\n".encode("latin-1"))
    assert lecture.erreur is None and lecture.tickets.loc[0, "text"] == "écran cassé"


def test_virgules_dans_le_texte_entre_guillemets():
    lecture = fichier.lire(b'text,team\n"Outlook crashes, then Teams too",x\n')
    assert lecture.tickets.loc[0, "text"] == "Outlook crashes, then Teams too"


def test_lignes_vides_ignorees():
    lecture = fichier.lire(b"text,id\nVPN down,1\n,2\n   ,3\nprinter offline,4\n")
    assert len(lecture.tickets) == 2


@pytest.mark.parametrize("octets, message", [
    (b"", "empty"),
    (b"description\nVPN down\n", "No text column"),
    (b"text\n\n", "empty"),
])
def test_fichiers_refuses(octets, message):
    lecture = fichier.lire(octets)
    assert lecture.tickets is None and message in lecture.erreur


def test_trop_gros(monkeypatch):
    monkeypatch.setattr(fichier, "MAX_OCTETS", 10)
    assert "too large" in fichier.lire(b"text\nVPN keeps disconnecting\n").erreur


def test_trop_de_lignes(monkeypatch):
    monkeypatch.setattr(fichier, "MAX_LIGNES", 3)
    lecture = fichier.lire(("text\n" + "VPN down\n" * 5).encode())
    assert len(lecture.tickets) == 3 and "first 3 tickets of 5" in lecture.avertissement


# --- Résultats ---

def aide(label="reseau", motif="solution", article=True, ok=True):
    return client.Reponse(ok, label=label, score=0.9, priorite="medium", decision="escalade" if motif == "critique"
                          else "solution", motif=motif, groupe="Network",
                          article={"id": "KB-NET-01", "titre": "VPN", "etapes": ["a", "b"]} if article else None,
                          message="" if ok else client.REFUS, corps={"source": "modele"})


def test_resultats_une_ligne_par_ticket():
    tickets = pd.DataFrame({"text": ["VPN down", "ransomware", "x" * 3000]})
    table = fichier.resultats(tickets, [aide(), aide("securite", "critique"), aide(ok=False)])
    assert list(table.columns) == ["text", *fichier.COLONNES]
    assert table.loc[0, "article"] == "KB-NET-01 VPN" and table.loc[0, "steps"] == "a | b"
    assert list(table["critical"]) == ["no", "yes", None]
    assert table.loc[2, "category"] == client.REFUS
    assert list(fichier.critiques(table).index) == [1]


def test_un_fichier_deja_traite_peut_etre_rechargé():
    """Le fichier téléchargé, renvoyé tel quel : ses anciennes colonnes de résultat sont remplacées."""
    tickets = pd.DataFrame({"text": ["VPN down"], "category": ["old"], "critical": ["old"]})
    table = fichier.resultats(tickets, [aide()])
    assert list(table.columns).count("category") == 1 and table.loc[0, "critical"] == "no"


def test_csv_pour_excel():
    octets = fichier.en_csv(pd.DataFrame({"text": ["écran"]}))
    assert octets.startswith("﻿".encode("utf-8")) and "écran" in octets.decode("utf-8-sig")


# --- Avec l'API ---

@avec_modele
@pytest.fixture
def session(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setenv("SUPPORT_TICKETS", str(tmp_path / "tickets.jsonl"))
    with TestClient(app) as c:
        yield c


@avec_modele
def test_un_fichier_de_bout_en_bout(session):
    lecture = fichier.lire(b"text\nA ransomware message appeared on my screen, my files are encrypted\nprinter offline\n")
    textes = list(lecture.tickets["text"])
    vus = []
    reponses = client.assister_lot(session, textes, lambda fait, total: vus.append((fait, total)))
    assert vus == [(1, 2), (2, 2)]
    table = fichier.resultats(lecture.tickets, reponses)
    assert table.loc[0, "critical"] == "yes" and table.loc[0, "article"].startswith("KB-SEC-")
    assert table.loc[1, "critical"] == "no"
    assert session.get("/tickets").json() == []  # aucun ticket sans confirmation


@avec_modele
def test_tickets_critiques_crees_apres_confirmation(session):
    texte = "A ransomware message appeared on my screen and my files are encrypted"
    aide_api = client.assister(session, texte)
    crees = client.creer_tickets_critiques(session, [texte], [aide_api])
    assert crees[0].ok and crees[0].ticket["label"] == "securite"
    assert crees[0].ticket["groupe"] == "Security (SOC)"
    assert len(session.get("/tickets").json()) == 1
