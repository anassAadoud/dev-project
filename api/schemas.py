"""Contrats d'entrée et de sortie de l'API (Pydantic v2)."""
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

Categorie = Literal["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]
# TP4 : sous le seuil d'abstention, ou avec trop de mots inconnus, l'API ne tranche pas.
Label = Literal["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service",
                "INDETERMINE"]
Priorite = Literal["high", "medium", "low"]
Decision = Literal["solution", "escalade"]
# TP5 : le motif de la décision, un code que l'interface traduit pour l'utilisateur.
Motif = Literal["mots_inconnus", "confiance_basse", "priorite_haute", "sans_article", "article_escalade", "solution",
                "critique", "hors_sujet"]
# TP5.1 : la conversation. L'action de l'utilisateur, la phase où en est l'agent, et le code de sa
# réponse, que l'interface traduit en anglais (comme le motif du TP5).
# TP5.2 : choisir un des articles suggérés, répondre à une question de diagnostic.
Action = Literal["message", "resolu", "pas_resolu", "categorie", "demander_ticket", "confirmer_ticket",
                 "refuser_ticket", "choisir_article", "diagnostic"]
Phase = Literal["solution", "precision", "proposition_ticket", "resolu", "ticket"]
Code = Literal["solution", "autre_solution", "question_precision", "choisir_categorie", "reformuler", "critique",
               "deux_essais", "demande", "resolu", "ticket_cree", "ticket_refuse", "hors_sujet", "confirmer_categorie"]
Statut = Literal["ouvert", "en_cours", "resolu", "ferme"]
# TP5.1 : qui a choisi la catégorie : le modèle, la base de connaissances (second avis), ou personne.
# TP5.2 : hors_sujet, le modèle reconnaît un message qui n'est pas un incident informatique.
Source = Literal["modele", "base", "aucune", "hors_sujet"]

EXEMPLE = "My VPN keeps disconnecting every 10 minutes when I work from home"
# TP5.2 : chaque champ texte a une longueur maximale ; les identifiants sont courts.
Identifiant = Annotated[str, StringConstraints(max_length=40)]
Etape = Annotated[str, StringConstraints(max_length=500)]


def pas_que_des_blancs(valeur: str) -> str:
    """Même règle que predict() : un texte que str.strip() vide est refusé (TP4, étape B)."""
    if not valeur.strip():
        raise ValueError("texte vide : il ne contient que des blancs")
    return valeur


class PredictRequest(BaseModel):
    """Requête de classement d'un incident."""

    text: str = Field(..., min_length=1, max_length=2000, description="Description de l'incident, en anglais",
                      examples=[EXEMPLE])

    _texte_non_blanc = field_validator("text")(pas_que_des_blancs)


class PredictResponse(BaseModel):
    """Catégorie IT, confiance et priorité estimée."""

    label: Label = Field(..., description="Catégorie IT de l'incident, ou INDETERMINE sous le seuil d'abstention")
    score: float = Field(..., ge=0, le=1, description="Confiance de la catégorie prédite")
    priorite: Priorite = Field(..., description="Priorité estimée par le second modèle")
    connus: float = Field(..., ge=0, le=1, description="Part des mots du texte connus du modèle")
    text: str = Field(..., description="Aperçu du texte analysé (100 caractères)")
    source: Source = Field("modele", description="Qui a choisi la catégorie : le modèle, la base (second avis), "
                                                 "personne (INDETERMINE), ou hors_sujet (pas un incident informatique)")


class Article(BaseModel):
    """Un article de la base de connaissances, avec ses étapes."""

    id: str
    categorie: Categorie | None = Field(None, description="La catégorie de l'article (TP5.2 : toute la base est cherchée)")
    titre: str
    etapes: list[str]
    escalade_si: str = Field(..., description="Quand l'article lui-même demande un technicien")
    similarite: float = Field(..., ge=0, le=1)
    source: str | None = Field(None, description="La documentation officielle d'où viennent les étapes, s'il y en a une")


class AssistResponse(PredictResponse):
    """Le classement, la solution proposée, et la décision d'escalade avec sa raison."""

    decision: Decision = Field(..., description="solution : l'utilisateur essaie ; escalade : un technicien prend le relais")
    motif: Motif = Field(..., description="Le motif de la décision, sous forme de code (règles de la fiche cas1)")
    raison: str = Field(..., description="Pourquoi cette décision, en clair, pour le technicien")
    groupe: str = Field(..., description="Le groupe de techniciens qui recevra le ticket")
    article: Article | None = Field(None, description="L'article proposé, ou rien si aucun ne correspond")
    articles: list[Article] = Field(default_factory=list,
                                    description="Les 3 meilleurs articles de toute la base (TP5.2), même si le modèle hésite")


class TicketRequest(BaseModel):
    """Un ticket pré-rempli : le texte, et ce que /assist a déjà trouvé (facultatif)."""

    text: str = Field(..., min_length=1, max_length=2000, description="Description de l'incident", examples=[EXEMPLE])
    label: Label | None = Field(None, description="Catégorie ; recalculée par l'API si absente")
    priorite: Priorite | None = Field(None, description="Priorité ; recalculée par l'API si absente")
    article_id: Identifiant | None = Field(None, description="L'article déjà essayé par l'utilisateur")
    raison: str | None = Field(None, max_length=500, description="Pourquoi le ticket est créé")
    conversation_id: Identifiant | None = Field(None, description="La conversation d'origine : un seul ticket par conversation")

    _texte_non_blanc = field_validator("text")(pas_que_des_blancs)


class EssaiTicket(BaseModel):
    """Un article déjà essayé sans succès, recopié dans le ticket."""

    article_id: str
    titre: str
    etapes_faites: list[str] = Field(default_factory=list)


class Evenement(BaseModel):
    """Un changement de statut du ticket (le suivi)."""

    le: str
    statut: Statut
    commentaire: str | None = None


class Ticket(BaseModel):
    """Un ticket enregistré, avec son suivi (TP5.1)."""

    id: str
    cree_le: str
    statut: Statut
    text: str
    label: Label
    priorite: Priorite
    groupe: str
    article_id: str | None
    raison: str
    conversation_id: str | None = None
    resume: str | None = Field(None, description="Le résumé de la conversation, pour le technicien")
    essais: list[EssaiTicket] = Field(default_factory=list, description="Les articles déjà essayés")
    resolution: str | None = Field(None, description="Ce qui a réglé l'incident (rempli par le technicien)")
    historique: list[Evenement] = Field(default_factory=list)


class TicketUpdate(BaseModel):
    """Le technicien fait avancer le ticket : nouveau statut, commentaire, résolution."""

    statut: Statut
    commentaire: str | None = Field(None, max_length=2000)
    resolution: str | None = Field(None, max_length=2000)


class ChatRequest(BaseModel):
    """Un tour de conversation : un message, ou un clic sur un bouton de la page."""

    conversation_id: Identifiant | None = Field(None, description="Absent pour commencer une conversation")
    action: Action = "message"
    text: str | None = Field(None, min_length=1, max_length=2000, examples=[EXEMPLE])
    categorie: Categorie | None = Field(None, description="La catégorie choisie (action « categorie »)")
    etapes_faites: list[Etape] = Field(default_factory=list, max_length=20,
                                     description="Les étapes cochées (action « pas_resolu »)")
    article_id: str | None = Field(None, max_length=40, description="L'article suggéré choisi (action « choisir_article »)")
    question_id: str | None = Field(None, max_length=60, description="La question de diagnostic (action « diagnostic »)")
    option_id: str | None = Field(None, max_length=60, description="La réponse choisie (action « diagnostic »)")

    @field_validator("text")
    @classmethod
    def _texte_non_blanc(cls, valeur: str | None) -> str | None:
        return None if valeur is None else pas_que_des_blancs(valeur)

    @model_validator(mode="after")
    def _champs_de_l_action(self) -> "ChatRequest":
        if self.action == "message" and self.text is None:
            raise ValueError("l'action « message » demande un texte")
        if self.action == "categorie" and self.categorie is None:
            raise ValueError("l'action « categorie » demande une catégorie")
        if self.action == "choisir_article" and self.article_id is None:
            raise ValueError("l'action « choisir_article » demande un article_id")
        if self.action == "diagnostic" and (self.question_id is None or self.option_id is None):
            raise ValueError("l'action « diagnostic » demande question_id et option_id")
        if self.action != "message" and self.conversation_id is None:
            raise ValueError("seul un message peut commencer une conversation")
        return self


class TicketSemblable(BaseModel):
    """Le ticket passé le plus proche, et ce qui l'a réglé."""

    id: str
    text: str
    resolution: str
    similarite: float = Field(..., ge=0, le=1)
    source: str = Field(..., description="tickets de l'agent, ou historique Tobi-Bueck")


class OptionDiagnostic(BaseModel):
    id: str
    label: str


class QuestionDiagnostic(BaseModel):
    """Une question de diagnostic (TP5.2) : « seulement vous ou tout le bureau ? », avec ses réponses."""

    id: str
    question: str
    options: list[OptionDiagnostic]


class ChatResponse(BaseModel):
    """La réponse de l'agent pour un tour : la phase, le code du message, et ce qu'il faut afficher."""

    conversation_id: str
    tour: int
    phase: Phase
    code: Code
    label: Label
    score: float = Field(..., ge=0, le=1)
    priorite: Priorite
    categorie: Categorie | None
    article: Article | None
    suggestions: list[Article] = Field(default_factory=list,
                                       description="D'autres articles proches, que l'utilisateur peut choisir (TP5.2)")
    question: QuestionDiagnostic | None = Field(None, description="La question de diagnostic proposée (TP5.2)")
    categories: list[Categorie] = Field(default_factory=list,
                                        description="Les boutons de catégories, de la plus probable à la moins probable")
    choix: list[Action] = Field(..., description="Les actions possibles maintenant")
    tentatives: int
    essais: list[EssaiTicket]
    ticket: Ticket | None = None
    ticket_semblable: TicketSemblable | None = None
    reformulation: str | None = Field(None, description="Réponse reformulée par le LLM (option, désactivée par défaut)")


class FeedbackRequest(BaseModel):
    """L'avis de l'utilisateur sur une réponse de l'agent : utile ou pas."""

    conversation_id: Identifiant
    tour: int = Field(..., ge=1, le=1000)
    utile: bool
    commentaire: str | None = Field(None, max_length=500)


class Feedback(FeedbackRequest):
    id: str
    le: str
    code: Code


class StatsResponse(BaseModel):
    """Les chiffres de la page de statistiques."""

    conversations: int
    resolues_sans_ticket: int
    avec_ticket: int
    en_cours: int
    taux_resolution_sans_ticket: float | None = Field(..., description="résolues sans ticket / conversations terminées")
    categories: dict[str, int]
    tickets_par_statut: dict[str, int]
    avis_utiles: int
    avis_pas_utiles: int
    tentatives_moyennes: float | None


class HealthResponse(BaseModel):
    """Réponse de l'endpoint de santé."""

    status: str = Field(..., description="OK si le modèle et la base sont chargés")
    model: str = Field(..., description="Nom du modèle servi")
    articles: int = Field(..., description="Nombre d'articles dans la base de connaissances")
    llm: str = Field("off", description="Reformulation par un LLM : off (par défaut) ou le modèle Ollama utilisé")
