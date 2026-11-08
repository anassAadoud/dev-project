"""Tests des briques du TP5.1 hors API : le LLM optionnel, le ticket passé le plus proche,
le stockage, et la base de connaissances (exclusions, ordre des catégories)."""
import httpx
import pytest

import api.model  # noqa: F401  (met src/ sur le chemin d'import : historique, kb)
from api import llm, stockage

ARTICLE = {"id": "KB-NET-01", "titre": "VPN disconnects", "etapes": ["Restart the client", "Reconnect"]}


# --- Le LLM, en option ---

def test_llm_desactive_par_defaut(monkeypatch):
    monkeypatch.delenv("SUPPORT_LLM", raising=False)
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: pytest.fail("Ollama appelé alors qu'il est désactivé"))
    assert not llm.active() and llm.description() == "off"
    assert llm.reformuler("My VPN drops", ARTICLE) is None


def test_llm_sans_article(monkeypatch):
    monkeypatch.setenv("SUPPORT_LLM", "ollama")
    assert llm.reformuler("My VPN drops", None) is None


@pytest.mark.parametrize("reponse", [
    httpx.ConnectError("Ollama absent"),
    httpx.Response(500, json={}),
    httpx.Response(200, json={"response": "   "}),
    httpx.Response(200, content=b"pas du json"),
])
def test_llm_en_panne_rend_none(monkeypatch, reponse):
    def faux_post(url, json, timeout):
        if isinstance(reponse, Exception):
            raise reponse
        reponse.request = httpx.Request("POST", url)
        return reponse

    monkeypatch.setenv("SUPPORT_LLM", "ollama")
    monkeypatch.setenv("SUPPORT_LLM_MODELE", "mistral")
    monkeypatch.setattr(llm.httpx, "post", faux_post)
    assert llm.reformuler("My VPN drops", ARTICLE) is None
    assert llm.description() == "ollama (mistral)"


# --- Le ticket passé le plus proche ---

PASSES = [
    {"id": "T1", "text": "VPN disconnects every hour from home", "categorie": "reseau",
     "resolution": "Reinstalled the VPN profile", "source": "agent tickets"},
    {"id": "T2", "text": "Printer offline on the second floor", "categorie": "materiel",
     "resolution": "Replaced the network cable", "source": "agent tickets"},
    {"id": "T3", "text": "VPN client error 809", "categorie": "reseau", "resolution": None, "source": "agent tickets"},
]


def test_plus_semblable():
    from historique import plus_semblable

    trouve = plus_semblable("My VPN disconnects from home", PASSES)
    assert trouve["id"] == "T1" and trouve["resolution"] == "Reinstalled the VPN profile"
    assert 0 < trouve["similarite"] <= 1


def test_plus_semblable_meme_categorie_et_seuil():
    from historique import plus_semblable

    assert plus_semblable("My VPN disconnects from home", PASSES, "materiel") is None  # sous le seuil
    assert plus_semblable("anything", [], None) is None
    assert plus_semblable("   ", PASSES) is None
    assert plus_semblable("the and of", [{**PASSES[0], "text": "the and of"}]) is None  # que des mots vides


def test_historique_absent_puis_construit(monkeypatch, tmp_path):
    import historique

    monkeypatch.setattr(historique, "HISTORIQUE", tmp_path / "absent.csv")
    historique.charger_historique.cache_clear()
    try:
        assert historique.charger_historique() == ()
        fichier = tmp_path / "historique.csv"
        fichier.write_text("text,categorie,answer\nVPN drops,reseau,Reinstall the client\nNo answer,reseau,\n",
                           encoding="utf-8")
        monkeypatch.setattr(historique, "HISTORIQUE", fichier)
        historique.charger_historique.cache_clear()
        passes = historique.charger_historique()
        assert len(passes) == 1 and passes[0]["source"] == "Tobi-Bueck history"
    finally:
        historique.charger_historique.cache_clear()


# --- Le stockage ---

def test_stockage_derniere_version(monkeypatch, tmp_path):
    monkeypatch.setenv("SUPPORT_TICKETS", str(tmp_path / "tickets.jsonl"))
    assert stockage.tous("feedback") == [] and stockage.lire("conversations", "X") is None
    stockage.ajouter("conversations", {"id": "A", "v": 1})
    stockage.ajouter("conversations", {"id": "B", "v": 1})
    stockage.ajouter("conversations", {"id": "A", "v": 2})
    assert stockage.tous("conversations") == [{"id": "A", "v": 2}, {"id": "B", "v": 1}]
    assert stockage.chemin("conversations") == tmp_path / "conversations.jsonl"
    with pytest.raises(ValueError, match="inconnue"):
        stockage.chemin("secrets")


# --- La base de connaissances ---

def test_base_au_moins_cinq_articles_par_categorie():
    from collections import Counter

    from kb import CATEGORIES, charger_base

    articles = charger_base()[0]
    par_categorie = Counter(a["categorie"] for a in articles)
    assert all(par_categorie[c] >= 5 for c in CATEGORIES), par_categorie
    assert len({a["id"] for a in articles}) == len(articles)  # identifiants uniques
    assert all(len(a["etapes"].split("|")) >= 3 for a in articles)


def test_chercher_exclut_les_articles_essayes():
    from kb import chercher

    premier = chercher("My VPN keeps disconnecting from home", "reseau")
    second = chercher("My VPN keeps disconnecting from home", "reseau", exclus=[premier["id"]])
    assert premier["id"] == "KB-NET-01" and (second is None or second["id"] != premier["id"])


def test_categories_proches():
    from kb import CATEGORIES, categories_proches

    ordre = categories_proches("The printer shows offline and nothing prints")
    assert ordre[0] == "materiel" and sorted(ordre) == sorted(CATEGORIES)
    assert categories_proches("zzzz") == CATEGORIES  # aucun mot commun : l'ordre par défaut
