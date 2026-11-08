"""Le jeu d'or : nos incidents, écrits à la main, vérifiés à chaque commit (TP4, étape C).

Un incident échoue si l'API se trompe franchement (une catégorie au lieu d'une autre).
Une abstention (INDETERMINE) ne le fait pas échouer : l'incident part vers un humain, ce
qui est le comportement voulu ; elle est comptée par src/bilan_jeu_or.py. Une erreur
connue reste dans le jeu, déclarée dans la colonne erreur_connue : le test devient
xfail(strict=True) et signalera sa correction.
"""
import csv
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
JEU_OR = RACINE / "data" / "jeu_or.csv"
MODELE = RACINE / "models" / "support.joblib"
FRANCHES = {"securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"}
MINIMUM_INCIDENTS, MINIMUM_DIFFICILES = 20, 5


def lire_jeu_or() -> list[dict[str, str]]:
    if not JEU_OR.exists():
        return []
    with JEU_OR.open(encoding="utf-8", newline="") as f:
        return [ligne for ligne in csv.DictReader(f) if (ligne.get("text") or "").strip()]


LIGNES = lire_jeu_or()


def cas_du_jeu_or():
    for numero, ligne in enumerate(LIGNES, start=2):  # ligne 1 : l'en-tête
        raison = (ligne.get("erreur_connue") or "").strip()
        marques = [pytest.mark.xfail(strict=True, reason=raison)] if raison else []
        yield pytest.param(ligne["text"], ligne["attendu"], id=f"ligne-{numero}", marks=marques)


def test_jeu_or_complet():
    """20 incidents au moins, dont 5 difficiles, chacun avec une catégorie attendue valide."""
    assert len(LIGNES) >= MINIMUM_INCIDENTS, f"jeu d'or incomplet : {len(LIGNES)} incidents sur {MINIMUM_INCIDENTS}"
    difficiles = [ligne for ligne in LIGNES if (ligne.get("difficulte") or "").strip()]
    assert len(difficiles) >= MINIMUM_DIFFICILES, (
        f"{len(difficiles)} incidents difficiles sur {MINIMUM_DIFFICILES} (colonne difficulte)"
    )
    for ligne in LIGNES:
        assert ligne["attendu"] in FRANCHES, f"catégorie attendue invalide : {ligne['attendu']!r}"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    if not MODELE.exists():
        pytest.skip("modèle non produit : python src/train.py")
    from fastapi.testclient import TestClient

    from api.main import app

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SUPPORT_TICKETS", str(tmp_path_factory.mktemp("tickets") / "tickets.jsonl"))
        with TestClient(app) as c:
            yield c


@pytest.mark.parametrize("texte, attendu", list(cas_du_jeu_or()))
def test_pas_d_erreur_franche(client, texte, attendu):
    reponse = client.post("/predict", json={"text": texte})
    assert reponse.status_code == 200
    label = reponse.json()["label"]
    assert not (label in FRANCHES and label != attendu), f"erreur franche : {label} au lieu de {attendu}"
