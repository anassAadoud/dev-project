"""La politique de conversation du TP5.1, règle par règle, sans modèle ni base (comme test_escalade.py).

Les outils (modèle, base, création du ticket) sont remplacés par un faux : ces tests tournent
partout, CI comprise, et fixent la politique : jamais de ticket au premier message, une autre
solution ou une question avant le ticket, confirmation obligatoire, un seul ticket.
"""
import pytest

from api import conversation as cv
from api.conversation import ActionRefusee, avancer, nouvelle


def article(identifiant, titre="titre", categorie="reseau"):
    return {"id": identifiant, "categorie": categorie, "titre": titre, "etapes": ["one", "two", "three"],
            "escalade_si": "never", "similarite": 0.5}


class FauxOutils:
    """Un modèle à mots-clés et une petite base : deux articles réseau, un matériel, un sécurité."""

    BASE = {"reseau": [article("NET-1"), article("NET-2")], "materiel": [article("HW-1", categorie="materiel")],
            "securite": [article("SEC-1", categorie="securite")],
            "panne_service": [article("OUT-1", categorie="panne_service")]}

    def __init__(self):
        self.tickets = []

    def predict(self, text):
        t = text.lower()
        priorite = "high" if "urgent" in t else "medium"
        for mot, label in [("vpn", "reseau"), ("printer", "materiel"), ("phishing", "securite"),
                           ("outage", "panne_service"), ("invoice", "facturation")]:
            if mot in t:
                return {"label": label, "score": 0.9, "priorite": priorite, "connus": 0.9}
        connus = 0.1 if "xqz" in t else 0.9
        return {"label": "INDETERMINE", "score": 0.3, "priorite": priorite, "connus": connus}

    QUESTIONS = {"reseau": [{"id": "portee", "question": "Only you?", "options": [
        {"id": "moi", "label": "Only me", "effet": {"articles": ["NET-2"]}},
        {"id": "tous", "label": "Everyone", "effet": {"categorie": "panne_service"}}]}]}

    def proposer(self, text, categorie, exclus, preferes):
        """Toute la base : la catégorie d'abord, les articles préférés devant ; sans catégorie, tout."""
        if "nothing" in text.lower():
            return []
        tous = [a for c, liste in self.BASE.items() for a in liste if a["id"] not in set(exclus)]
        tous.sort(key=lambda a: (a["id"] not in preferes, a["categorie"] != categorie))
        return tous[:3] if categorie is None or any(a["categorie"] == categorie for a in tous) else []

    def questions(self, categorie):
        return self.QUESTIONS.get(categorie, [])

    def creer_ticket_conversation(self, conv):
        self.tickets.append(dict(conv))
        return {"id": f"TCK-{len(self.tickets)}"}


@pytest.fixture
def outils():
    return FauxOutils()


def debut(outils, texte):
    return avancer(nouvelle("CNV-TEST"), "message", outils, texte=texte)


@pytest.mark.parametrize("texte", [
    "My VPN keeps disconnecting",                       # cas simple
    "Urgent: my VPN keeps disconnecting",               # priorité haute
    "Something odd happens on my computer",             # le modèle hésite
    "xqz wlk grb",                                      # mots inconnus
    "I received a phishing email",                      # critique
    "The outage blocks everyone",                       # panne générale
    "Please open a ticket, my VPN fails",               # demande explicite
    "The printer shows nothing at all",                 # aucun article
])
def test_jamais_de_ticket_au_premier_message(outils, texte):
    conv = debut(outils, texte)
    assert outils.tickets == [] and conv["ticket_id"] is None and conv["phase"] != "ticket"


def test_solution_puis_resolu_sans_ticket(outils):
    conv = debut(outils, "My VPN keeps disconnecting")
    assert (conv["phase"], conv["code"], conv["article"]["id"]) == ("solution", "solution", "NET-1")
    assert {"resolu", "pas_resolu", "demander_ticket"} <= set(cv.actions_possibles(conv))
    conv = avancer(conv, "resolu", outils)
    assert (conv["phase"], conv["code"]) == ("resolu", "resolu")
    assert outils.tickets == [] and cv.actions_possibles(conv) == []


def test_la_priorite_haute_ne_cree_plus_de_ticket(outils):
    conv = debut(outils, "Urgent: my VPN keeps disconnecting")
    assert conv["phase"] == "solution" and conv["priorite"] == "high"


def test_pas_resolu_une_fois_donne_un_autre_article(outils):
    conv = avancer(debut(outils, "My VPN keeps disconnecting"), "pas_resolu", outils, etapes_faites=["one"])
    assert (conv["phase"], conv["code"], conv["article"]["id"]) == ("solution", "autre_solution", "NET-2")
    assert conv["tentatives"] == 1 and conv["essais"][0] == {"article_id": "NET-1", "titre": "titre",
                                                             "etapes_faites": ["one"]}


def test_deux_tentatives_proposent_le_ticket_sans_le_creer(outils):
    conv = debut(outils, "My VPN keeps disconnecting")
    conv = avancer(conv, "pas_resolu", outils)
    conv = avancer(conv, "pas_resolu", outils, etapes_faites=["one", "two"])
    assert (conv["phase"], conv["code"], conv["tentatives"]) == ("proposition_ticket", "deux_essais", 2)
    assert outils.tickets == []  # proposé, pas créé : il faut la confirmation
    assert "confirmer_ticket" in cv.actions_possibles(conv)
    conv = avancer(conv, "confirmer_ticket", outils)
    assert (conv["phase"], conv["code"], conv["ticket_id"]) == ("ticket", "ticket_cree", "TCK-1")
    assert [e["article_id"] for e in outils.tickets[0]["essais"]] == ["NET-1", "NET-2"]
    assert cv.raison_du_ticket(conv) == cv.RAISONS["deux_essais"]


def test_sans_autre_article_une_question_de_precision(outils):
    conv = avancer(debut(outils, "The printer is offline"), "pas_resolu", outils)
    assert (conv["phase"], conv["code"], conv["article"]) == ("precision", "question_precision", None)
    assert conv["tentatives"] == 1
    # La précision ne mène à rien : seconde tentative perdue, le ticket est proposé.
    conv = avancer(conv, "message", outils, texte="The printer still shows nothing")
    assert (conv["phase"], conv["code"], conv["tentatives"]) == ("proposition_ticket", "deux_essais", 2)


def test_la_precision_peut_mener_a_un_article(outils):
    conv = debut(outils, "It does not work again")
    assert (conv["phase"], conv["code"]) == ("precision", "choisir_categorie")
    conv = avancer(conv, "message", outils, texte="My VPN does not connect from home")
    assert (conv["phase"], conv["code"], conv["article"]["id"]) == ("solution", "solution", "NET-1")
    assert conv["textes"] == ["It does not work again", "My VPN does not connect from home"]


def test_aucun_article_au_premier_message_une_question(outils):
    conv = debut(outils, "The printer shows nothing at all")
    assert (conv["phase"], conv["code"], conv["tentatives"]) == ("precision", "question_precision", 0)


def test_le_modele_hesite_boutons_de_categories(outils):
    conv = debut(outils, "Something odd happens on my computer")
    assert (conv["phase"], conv["code"], conv["categorie"]) == ("precision", "choisir_categorie", None)
    assert "categorie" in cv.actions_possibles(conv)
    conv = avancer(conv, "categorie", outils, categorie="materiel")
    assert (conv["phase"], conv["code"], conv["article"]["id"]) == ("solution", "solution", "HW-1")
    assert conv["categorie_choisie"] and outils.tickets == []


def test_la_categorie_choisie_reste_celle_de_l_utilisateur(outils):
    conv = avancer(debut(outils, "Something odd happens"), "categorie", outils, categorie="materiel")
    conv = avancer(conv, "message", outils, texte="also my VPN is slow")
    assert conv["categorie"] == "materiel"


def test_hors_sujet_explique_et_propose_les_boutons(outils, monkeypatch):
    """TP5.2 : un message hors sujet ; l'agent le dit, sans ticket, et laisse choisir une catégorie."""
    monkeypatch.setattr(outils, "predict", lambda t: {"label": "INDETERMINE", "score": 0.9, "priorite": "low",
                                                      "connus": 0.9, "source": "hors_sujet"})
    conv = debut(outils, "how do I make mint tea")
    assert (conv["phase"], conv["code"]) == ("precision", "hors_sujet") and outils.tickets == []
    assert "categorie" in cv.actions_possibles(conv)


def test_mots_inconnus_reformuler(outils):
    conv = debut(outils, "xqz wlk grb")
    assert (conv["phase"], conv["code"]) == ("precision", "reformuler")


def test_categorie_sans_article_une_question(outils):
    conv = avancer(debut(outils, "Something odd"), "categorie", outils, categorie="facturation")
    assert (conv["phase"], conv["code"], conv["tentatives"]) == ("precision", "question_precision", 1)


@pytest.mark.parametrize("texte, categorie", [("I received a phishing email", "securite"),
                                              ("The outage blocks everyone", "panne_service")])
def test_cas_critique_propose_le_ticket_avec_les_etapes(outils, texte, categorie):
    conv = debut(outils, texte)
    assert (conv["phase"], conv["code"], conv["categorie"]) == ("proposition_ticket", "critique", categorie)
    assert conv["article"] is not None  # les étapes à faire en attendant le technicien
    assert outils.tickets == []
    conv = avancer(conv, "confirmer_ticket", outils)
    assert conv["phase"] == "ticket" and cv.raison_du_ticket(conv) == cv.RAISONS["critique"]


def test_critique_refuse_l_utilisateur_essaie_les_etapes(outils):
    conv = avancer(debut(outils, "I received a phishing email"), "refuser_ticket", outils)
    assert (conv["phase"], conv["code"]) == ("solution", "ticket_refuse")
    conv = avancer(conv, "resolu", outils)
    assert conv["phase"] == "resolu" and outils.tickets == []


def test_critique_choisi_par_bouton(outils):
    conv = avancer(debut(outils, "Something odd"), "categorie", outils, categorie="securite")
    assert (conv["phase"], conv["code"]) == ("proposition_ticket", "critique")


def test_critique_resolu_pendant_la_proposition(outils):
    conv = avancer(debut(outils, "I received a phishing email"), "resolu", outils)
    assert conv["phase"] == "resolu" and outils.tickets == []


def test_demande_dans_le_texte(outils):
    conv = debut(outils, "Please open a ticket, my VPN fails")
    assert (conv["phase"], conv["code"]) == ("proposition_ticket", "demande")
    assert conv["article"]["id"] == "NET-1"  # les étapes restent visibles
    assert outils.tickets == []
    conv = avancer(conv, "confirmer_ticket", outils)
    assert conv["phase"] == "ticket" and cv.raison_du_ticket(conv) == cv.RAISONS["demande"]


def test_demande_par_le_bouton(outils):
    conv = avancer(debut(outils, "My VPN keeps disconnecting"), "demander_ticket", outils)
    assert (conv["phase"], conv["code"]) == ("proposition_ticket", "demande") and outils.tickets == []


def test_demande_dans_un_message_suivant(outils):
    conv = debut(outils, "Something odd happens")
    conv = avancer(conv, "message", outils, texte="I want to talk to a human")
    assert (conv["phase"], conv["code"]) == ("proposition_ticket", "demande")


def test_ticket_refuse_sans_article_retour_aux_questions(outils):
    conv = debut(outils, "My VPN keeps disconnecting")
    conv = avancer(avancer(conv, "pas_resolu", outils), "pas_resolu", outils)
    conv = avancer(conv, "refuser_ticket", outils)
    assert (conv["phase"], conv["code"]) == ("precision", "ticket_refuse") and outils.tickets == []
    conv = avancer(conv, "message", outils, texte="the VPN shows nothing new")
    assert (conv["phase"], conv["code"]) == ("proposition_ticket", "deux_essais")


def test_un_seul_ticket_par_conversation(outils):
    conv = avancer(debut(outils, "Please open a ticket, my VPN fails"), "confirmer_ticket", outils)
    with pytest.raises(ActionRefusee, match="un seul ticket"):
        avancer(conv, "confirmer_ticket", outils)
    with pytest.raises(ActionRefusee, match="un seul ticket"):
        avancer(conv, "demander_ticket", outils)
    assert len(outils.tickets) == 1


@pytest.mark.parametrize("action", ["confirmer_ticket", "refuser_ticket", "categorie"])
def test_action_impossible_dans_cette_phase(outils, action):
    with pytest.raises(ActionRefusee, match="impossible"):
        avancer(debut(outils, "My VPN keeps disconnecting"), action, outils)


def test_rien_apres_une_conversation_resolue(outils):
    conv = avancer(debut(outils, "My VPN keeps disconnecting"), "resolu", outils)
    with pytest.raises(ActionRefusee):
        avancer(conv, "message", outils, texte="hello again")


@pytest.mark.parametrize("action", ["resolu", "confirmer_ticket", "categorie"])
def test_une_conversation_commence_par_un_message(outils, action):
    with pytest.raises(ActionRefusee, match="commence"):
        avancer(nouvelle("CNV-X"), action, outils, categorie="reseau")


def test_message_vide_ou_categorie_absente_refuses(outils):
    with pytest.raises(ActionRefusee, match="texte"):
        avancer(nouvelle("CNV-X"), "message", outils, texte="  ")
    with pytest.raises(ActionRefusee, match="catégorie"):
        avancer(debut(outils, "Something odd"), "categorie", outils)


def test_les_tours_sont_numerotes(outils):
    conv = avancer(debut(outils, "My VPN keeps disconnecting"), "pas_resolu", outils)
    assert [(t["tour"], t["action"], t["code"]) for t in conv["tours"]] == [
        (1, "message", "solution"), (2, "pas_resolu", "autre_solution")]


@pytest.mark.parametrize("texte, attendu", [
    ("Please open a ticket for me", True),
    ("I need a technician: the monitor is broken", True),
    ("Can I speak to someone?", True),
    ("I want to talk to a human", True),
    ("Please create a support ticket", True),
    ("Someone logged into my account from an unknown country", False),
    ("The ticketing portal is still down", False),
    ("My VPN keeps disconnecting", False),
])
def test_demande_humain(texte, attendu):
    assert cv.demande_humain(texte) is attendu


def test_resume_court_avec_les_details():
    conv = nouvelle("CNV-X")
    conv["textes"] = ["x" * 300, "the VPN client shows error 809"]
    resume = cv.resumer(conv)
    assert resume.startswith("x" * 100) and "…" in resume and "error 809" in resume and len(resume) < 300


def test_raison_par_defaut():
    assert cv.raison_du_ticket(nouvelle("CNV-X")) == cv.RAISONS["demande"]


def test_meme_seuil_de_vocabulaire_que_l_api():
    from api.model import SEUIL_VOCABULAIRE

    assert cv.SEUIL_VOCABULAIRE == SEUIL_VOCABULAIRE
