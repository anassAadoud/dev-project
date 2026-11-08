"""Contrats d'entrée et de sortie de l'API (Pydantic v2)."""
from typing import Literal

from pydantic import BaseModel, Field

Label = Literal["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]
Priorite = Literal["high", "medium", "low"]
Decision = Literal["solution", "escalade"]

EXEMPLE = "My VPN keeps disconnecting every 10 minutes when I work from home"


class PredictRequest(BaseModel):
    """Requête de classement d'un incident."""

    text: str = Field(..., min_length=1, max_length=2000, description="Description de l'incident, en anglais",
                      examples=[EXEMPLE])


class PredictResponse(BaseModel):
    """Catégorie IT, confiance et priorité estimée."""

    label: Label = Field(..., description="Catégorie IT de l'incident")
    score: float = Field(..., ge=0, le=1, description="Confiance de la catégorie prédite")
    priorite: Priorite = Field(..., description="Priorité estimée par le second modèle")
    text: str = Field(..., description="Aperçu du texte analysé (100 caractères)")


class Article(BaseModel):
    """Un article de la base de connaissances, avec ses étapes."""

    id: str
    titre: str
    etapes: list[str]
    escalade_si: str = Field(..., description="Quand l'article lui-même demande un technicien")
    similarite: float = Field(..., ge=0, le=1)


class AssistResponse(PredictResponse):
    """Le classement, la solution proposée, et la décision d'escalade avec sa raison."""

    decision: Decision = Field(..., description="solution : l'utilisateur essaie ; escalade : un technicien prend le relais")
    raison: str = Field(..., description="Pourquoi cette décision (règles de la fiche cas1)")
    groupe: str = Field(..., description="Le groupe de techniciens qui recevra le ticket")
    article: Article | None = Field(None, description="L'article proposé, ou rien si aucun ne correspond")


class TicketRequest(BaseModel):
    """Un ticket pré-rempli : le texte, et ce que /assist a déjà trouvé (facultatif)."""

    text: str = Field(..., min_length=1, max_length=2000, description="Description de l'incident", examples=[EXEMPLE])
    label: Label | None = Field(None, description="Catégorie ; recalculée par l'API si absente")
    priorite: Priorite | None = Field(None, description="Priorité ; recalculée par l'API si absente")
    article_id: str | None = Field(None, description="L'article déjà essayé par l'utilisateur")
    raison: str | None = Field(None, description="Pourquoi le ticket est créé")


class Ticket(BaseModel):
    """Un ticket enregistré."""

    id: str
    cree_le: str
    statut: Literal["ouvert"]
    text: str
    label: Label
    priorite: Priorite
    groupe: str
    article_id: str | None
    raison: str


class HealthResponse(BaseModel):
    """Réponse de l'endpoint de santé."""

    status: str = Field(..., description="OK si le modèle et la base sont chargés")
    model: str = Field(..., description="Nom du modèle servi")
    articles: int = Field(..., description="Nombre d'articles dans la base de connaissances")
