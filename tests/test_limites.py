"""Tests aux limites du contrat d'entrée (TP4, étape B).

PredictRequest promet un champ « text », chaîne de 1 à 2000 caractères qui ne soit pas faite que de blancs.
Ce fichier vérifie cette promesse à ses frontières, puis au hasard (hypothesis). Chaque refus doit avoir la forme
standard de FastAPI. Les mêmes règles valent pour /assist, qui reçoit le même corps.
"""
import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

MODELE = Path(__file__).resolve().parents[1] / "models" / "support.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")

ETIQUETTES = {"securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service",
              "INDETERMINE"}

# Les caractères que str.strip() retire : la règle de predict(), reprise par le schéma.
BLANCS = "".join(c for c in map(chr, range(0x110000)) if c.isspace())


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """Portée « module » : l'API démarre une fois pour tout le fichier (hypothesis l'exige)."""
    from fastapi.testclient import TestClient

    from api.main import app

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUPPORT_TICKETS", str(tmp_path_factory.mktemp("tickets") / "tickets.jsonl"))
        with TestClient(app) as c:  # le « with » exécute le lifespan : le modèle est chargé
            yield c


def en_json(valeur: object) -> bytes:
    """Corps de requête JSON, sous forme d'octets : permet aussi d'envoyer un corps invalide."""
    return json.dumps(valeur).encode("utf-8")


def verifier_forme_422(reponse, type_attendu: str | None = None) -> None:
    """Un 422 porte la liste d'erreurs standard de FastAPI : des objets avec loc, msg, type."""
    detail = reponse.json()["detail"]
    assert isinstance(detail, list) and detail, f"detail n'est pas une liste d'erreurs : {detail!r}"
    for erreur in detail:
        assert {"loc", "msg", "type"} <= erreur.keys(), f"erreur mal formée : {erreur!r}"
    if type_attendu is not None:
        assert detail[0]["type"] == type_attendu, detail


# Étape B.1 : huit cas aux frontières, avec le code et, pour un 422, le type d'erreur attendu.
CAS = [
    pytest.param(en_json({"text": ""}), 422, "string_too_short", id="texte-vide"),
    pytest.param(en_json({"text": "   "}), 422, "value_error", id="texte-espaces"),
    pytest.param(en_json({"text": "a"}), 200, None, id="un-caractere"),
    pytest.param(en_json({"text": "a" * 2000}), 200, None, id="2000-caracteres"),
    pytest.param(en_json({"text": "a" * 2001}), 422, "string_too_long", id="2001-caracteres"),
    pytest.param(en_json({}), 422, "missing", id="champ-absent"),
    pytest.param(en_json({"text": 42}), 422, "string_type", id="autre-type"),
    pytest.param(b"pas du json", 422, "json_invalid", id="pas-du-json"),
]


@pytest.mark.parametrize("corps, code_attendu, type_attendu", CAS)
def test_frontieres_du_contrat(client, corps, code_attendu, type_attendu):
    reponse = client.post("/predict", content=corps, headers={"Content-Type": "application/json"})
    assert reponse.status_code == code_attendu, reponse.text
    if code_attendu == 422:
        verifier_forme_422(reponse, type_attendu)  # Étape B.2 : la forme du refus
    else:
        assert reponse.json()["label"] in ETIQUETTES


# Étape B.5 : deux propriétés, vérifiées sur des textes tirés au hasard.
@settings(deadline=None, max_examples=60)
@given(texte=st.text(min_size=1, max_size=2000).filter(lambda t: t.strip() != ""))
def test_tout_texte_non_blanc_est_accepte(client, texte):
    reponse = client.post("/predict", json={"text": texte})
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["label"] in ETIQUETTES
    assert 0 <= corps["score"] <= 1


@settings(deadline=None, max_examples=60)
@given(texte=st.text(alphabet=BLANCS, min_size=1, max_size=50))
def test_tout_texte_de_blancs_est_refuse(client, texte):
    reponse = client.post("/predict", json={"text": texte})
    assert reponse.status_code == 422
    verifier_forme_422(reponse)
