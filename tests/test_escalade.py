"""Les règles d'escalade de la fiche cas1, une par une (TP4).

decider() ne dépend ni du modèle ni de la base : ces tests tournent partout, CI comprise.
Chaque règle de la fiche a son test ; l'ordre des règles est vérifié par le dernier.
"""
import pytest

from api.model import SEUIL_ABSTENTION, SEUIL_VOCABULAIRE, decider, decider_tp51

ARTICLE = {"id": "KB-NET-01", "titre": "VPN", "etapes": ["a", "b", "c"], "escalade_si": "the VPN still drops",
           "similarite": 0.4}


def prediction(label="reseau", score=0.9, priorite="medium", connus=1.0):
    return {"label": label, "score": score, "priorite": priorite, "connus": connus, "text": "..."}


def test_mots_inconnus_vont_au_tri():
    decision, motif, raison = decider(prediction(label="INDETERMINE", connus=SEUIL_VOCABULAIRE - 0.1), None)
    assert (decision, motif) == ("escalade", "mots_inconnus") and "mots" in raison


def test_confiance_basse_va_au_tri():
    decision, motif, raison = decider(prediction(label="INDETERMINE", score=SEUIL_ABSTENTION - 0.1), None)
    assert (decision, motif) == ("escalade", "confiance_basse") and "incertaine" in raison


def test_priorite_haute_escalade_meme_avec_un_article():
    decision, motif, raison = decider(prediction(priorite="high"), ARTICLE)
    assert (decision, motif) == ("escalade", "priorite_haute") and "priorité haute" in raison


def test_sans_article_on_escalade():
    decision, motif, raison = decider(prediction(), None)
    assert (decision, motif) == ("escalade", "sans_article") and "aucun article" in raison


def test_article_qui_demande_toujours_un_technicien():
    decision, motif, raison = decider(prediction(), {**ARTICLE, "escalade_si": "always: the billing team"})
    assert (decision, motif) == ("escalade", "article_escalade") and ARTICLE["id"] in raison


def test_sinon_la_solution_est_proposee():
    decision, motif, raison = decider(prediction(), ARTICLE)
    assert (decision, motif) == ("solution", "solution") and ARTICLE["id"] in raison


@pytest.mark.parametrize("priorite", ["low", "medium"])
def test_une_priorite_basse_n_empeche_jamais_l_abstention(priorite):
    """La priorité ne sert que dans un sens : un incident incertain va au tri, quelle que soit sa priorité."""
    assert decider(prediction(label="INDETERMINE", score=0.1, priorite=priorite), ARTICLE)[0] == "escalade"


# --- TP5.1 : la décision de /assist suit la politique de la conversation ---

def test_tp51_mots_inconnus_et_confiance_basse_vont_au_tri():
    assert decider_tp51(prediction(label="INDETERMINE", connus=0.1), None)[:2] == ("escalade", "mots_inconnus")
    assert decider_tp51(prediction(label="INDETERMINE", score=0.3), None)[:2] == ("escalade", "confiance_basse")


@pytest.mark.parametrize("label", ["securite", "panne_service"])
def test_tp51_cas_critique_escalade_meme_avec_un_article(label):
    assert decider_tp51(prediction(label=label), ARTICLE)[:2] == ("escalade", "critique")


def test_tp51_sans_article_escalade():
    assert decider_tp51(prediction(), None)[:2] == ("escalade", "sans_article")


def test_tp51_la_priorite_haute_ne_suffit_plus():
    assert decider_tp51(prediction(priorite="high"), ARTICLE)[:2] == ("solution", "solution")


def test_tp51_un_article_always_propose_d_abord_les_etapes():
    article = {**ARTICLE, "escalade_si": "always: the billing team"}
    assert decider_tp51(prediction(label="facturation"), article)[:2] == ("solution", "solution")
