"""Les vecteurs de phrases de l'hybride (TP5.2, phase 4).

Les tests rapides utilisent l'encodeur factice : ils tournent partout, CI comprise, sans téléchargement.
Le test marqué « lent » utilise le vrai all-MiniLM-L6-v2 ; il est ignoré si le modèle n'est pas dans le cache
Hugging Face du poste (la CI lance pytest -m "not lent").
"""
import pickle
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import encodeur  # noqa: E402
from encodeur import Phrases, mode_demande, mode_du_modele  # noqa: E402


def test_factice_dimension_normalise_et_deterministe():
    vecteurs = Phrases(1.0, "factice").fit([]).transform(["VPN keeps dropping", "invoice is wrong"]).toarray()
    assert vecteurs.shape == (2, encodeur.DIMENSION)
    assert np.allclose(np.linalg.norm(vecteurs, axis=1), 1.0)
    encore = Phrases(1.0, "factice").transform(["VPN keeps dropping"]).toarray()
    assert np.allclose(encore[0], vecteurs[0])


def test_le_poids_multiplie_les_vecteurs():
    un = Phrases(1.0, "factice").transform(["printer offline"]).toarray()
    deux = Phrases(2.0, "factice").transform(["printer offline"]).toarray()
    assert np.allclose(deux, 2 * un)


def test_le_mode_est_garde_dans_le_modele(monkeypatch):
    """Le mode est choisi à l'entraînement : changer SUPPORT_ENCODEUR ensuite ne change pas un modèle entraîné."""
    monkeypatch.setenv("SUPPORT_ENCODEUR", "factice")
    etape = Phrases(1.0).fit(["a"])
    copie = pickle.loads(pickle.dumps(etape))
    monkeypatch.setenv("SUPPORT_ENCODEUR", "minilm")
    assert copie.mode == "factice"


@pytest.mark.parametrize("valeur, attendu", [(None, "minilm"), ("factice", "factice"), (" MiniLM ", "minilm")])
def test_mode_demande(monkeypatch, valeur, attendu):
    if valeur is None:
        monkeypatch.delenv("SUPPORT_ENCODEUR", raising=False)
    else:
        monkeypatch.setenv("SUPPORT_ENCODEUR", valeur)
    assert mode_demande() == attendu


def test_mode_inconnu_refuse(monkeypatch):
    monkeypatch.setenv("SUPPORT_ENCODEUR", "bert")
    with pytest.raises(ValueError, match="bert"):
        mode_demande()


def test_le_cache_est_borne(monkeypatch):
    monkeypatch.setattr(encodeur, "TAILLE_CACHE", 5)
    Phrases._cache.clear()
    Phrases(1.0, "factice").transform([f"message {i}" for i in range(12)])
    assert len(Phrases._cache) == 5


def test_mode_du_modele():
    import train

    avec = train.construire_pipeline(phrases=True)
    sans = train.construire_pipeline(phrases=False)
    assert mode_du_modele(avec) in {"minilm", "factice"}
    assert mode_du_modele(sans) is None


def test_encodeur_indisponible_message_clair(monkeypatch):
    """Sans sentence-transformers (ou sans le modèle), l'erreur dit quoi faire."""
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    monkeypatch.setattr(Phrases, "_modeles", {})
    with pytest.raises(encodeur.EncodeurIndisponible, match="--sans-minilm"):
        Phrases(1.0, "minilm").transform(["texte jamais encodé 7f3a"])


def minilm_en_cache() -> bool:
    try:
        from huggingface_hub import try_to_load_from_cache

        return isinstance(try_to_load_from_cache(encodeur.NOM_MINILM, "config.json"), str)
    except Exception:
        return False


@pytest.mark.lent
@pytest.mark.skipif(not minilm_en_cache(), reason="all-MiniLM-L6-v2 absent du cache Hugging Face")
def test_lent_le_vrai_minilm_rapproche_les_paraphrases(monkeypatch):
    """Le vrai encodeur : deux formulations du même incident sont plus proches qu'un autre incident,
    même sans mot commun (c'est ce que les TF-IDF ne savent pas faire)."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    etape = Phrases(1.0, "minilm")
    a, b, c = etape.transform(["my laptop will not power on",
                               "the computer stays black when I press the start button",
                               "we were charged twice on the invoice"]).toarray()
    assert a.shape == (encodeur.DIMENSION,)
    assert float(a @ b) > float(a @ c) + 0.1
