"""API REST de l'agent de support informatique (TP3 ; conversation, suivi et statistiques au TP5.1).

Lancer : uvicorn api.main:app --reload
Doc    : http://localhost:8000/docs
"""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api import llm, stockage, suivi, tickets
from api.conversation import ActionRefusee
from api.model import GROUPES, Assistance, ConversationInconnue, Prediction, SupportClassifier, load_model
from api.schemas import (
    AssistResponse,
    ChatRequest,
    ChatResponse,
    Feedback,
    FeedbackRequest,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    StatsResponse,
    Ticket,
    TicketRequest,
    TicketUpdate,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("support_api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Charge le modèle et la base une seule fois, avant la première requête."""
    logger.info("Démarrage de l'API...")
    app.state.classifier = load_model()
    logger.info("Modèle chargé avec succès : %s ; %d articles", app.state.classifier.model_name,
                app.state.classifier.articles)
    yield
    logger.info("Arrêt de l'API")


app = FastAPI(
    title="IT Support Agent API",
    description="Converse avec l'utilisateur sur un incident informatique décrit en anglais : classe "
                "l'incident, propose les solutions de la base de connaissances pas à pas, et ne crée un "
                "ticket que si c'est nécessaire, après confirmation (modèle du TP2, politique du TP5.1).",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS : indispensable pour un frontend web (TP5). En production, lister les domaines autorisés.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _classifier() -> SupportClassifier:
    clf: SupportClassifier | None = getattr(app.state, "classifier", None)
    if clf is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    return clf


@app.get("/", summary="Accueil")
async def root() -> dict[str, str]:
    return {"message": "IT Support Agent API", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, summary="Santé de l'API")
async def health_check() -> dict:
    """Répond 200 si le modèle et la base sont chargés, 503 sinon."""
    clf = _classifier()
    return {"status": "OK", "model": clf.model_name, "articles": clf.articles, "llm": llm.description()}


@app.post("/predict", response_model=PredictResponse, summary="Classer un incident")
async def predict(request: PredictRequest) -> Prediction:
    """Renvoie la catégorie IT (ou INDETERMINE), la confiance, la priorité et la part de mots connus.

    - 422 : texte refusé par le contrat (vide, que des blancs, plus de 2000 caractères)
    - 503 : modèle non chargé
    - 500 : erreur inattendue (journalisée côté serveur, jamais renvoyée au client)
    """
    clf = _classifier()
    try:
        result = clf.predict(request.text)
    except Exception:
        # Le contrat a déjà refusé les textes invalides : toute exception ici est une panne (TP4, étape D).
        logger.exception("Erreur dans /predict")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur") from None
    logger.info("predict: %r -> %s (%.2f, %s)", request.text[:50], result["label"], result["score"], result["priorite"])
    return result


@app.post("/assist", response_model=AssistResponse, summary="Proposer une solution ou escalader")
async def assist(request: PredictRequest) -> Assistance:
    """Classe l'incident, propose l'article le plus proche de la base, et décide :
    « solution » (l'utilisateur essaie les étapes) ou « escalade » (vers le groupe indiqué)."""
    clf = _classifier()
    try:
        result = clf.assist(request.text)
    except Exception:
        # Le contrat a déjà refusé les textes invalides : toute exception ici est une panne (TP4, étape D).
        logger.exception("Erreur dans /assist")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur") from None
    logger.info("assist: %r -> %s, %s", request.text[:50], result["label"], result["decision"])
    return result


@app.post("/tickets", response_model=Ticket, status_code=201, summary="Créer un ticket pré-rempli")
async def creer_ticket(request: TicketRequest) -> dict:
    """Enregistre un ticket ouvert et l'affecte au groupe de sa catégorie.
    La catégorie et la priorité manquantes sont calculées par le modèle."""
    clf = _classifier()
    champs = request.model_dump()
    if champs["conversation_id"] and tickets.pour_conversation(champs["conversation_id"]) is not None:
        raise HTTPException(status_code=409, detail="Un seul ticket par conversation")
    if champs["label"] is None or champs["priorite"] is None:
        try:
            prediction = clf.predict(request.text)
        except Exception:
            logger.exception("Erreur dans /tickets")
            raise HTTPException(status_code=500, detail="Erreur interne du serveur") from None
        champs["label"] = champs["label"] or prediction["label"]
        champs["priorite"] = champs["priorite"] or prediction["priorite"]
    champs["groupe"] = GROUPES[champs["label"]]
    champs["raison"] = champs["raison"] or "ticket demandé par l'utilisateur"
    ticket = tickets.creer(champs)
    logger.info("ticket %s -> %s (%s)", ticket["id"], ticket["groupe"], ticket["priorite"])
    return ticket


@app.get("/tickets", response_model=list[Ticket], summary="Lister les tickets")
async def lister_tickets() -> list[dict]:
    """Tous les tickets, dans leur version actuelle (le plus ancien d'abord)."""
    return tickets.lister()


@app.get("/tickets/{identifiant}", response_model=Ticket, summary="Lire un ticket")
async def lire_ticket(identifiant: str) -> dict:
    """Renvoie le ticket, avec son statut et son historique, ou 404 s'il n'existe pas."""
    ticket = tickets.lire(identifiant)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    return ticket


@app.patch("/tickets/{identifiant}", response_model=Ticket, summary="Faire avancer un ticket")
async def suivre_ticket(identifiant: str, request: TicketUpdate) -> dict:
    """Le technicien change le statut (ouvert, en_cours, resolu, ferme) ; l'historique garde chaque étape."""
    ticket = tickets.mettre_a_jour(identifiant, request.statut, request.commentaire, request.resolution)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    logger.info("ticket %s -> %s", identifiant, request.statut)
    return ticket


@app.post("/chat", response_model=ChatResponse, summary="Un tour de conversation avec l'agent")
async def chat(request: ChatRequest) -> dict:
    """Commence une conversation (sans conversation_id) ou la continue.

    L'agent répond d'abord avec un article de la base, demande si c'est résolu, propose un autre
    article ou pose une question de précision, et ne propose le ticket qu'après deux tentatives,
    sur demande, ou pour un cas critique ; il le crée seulement quand l'utilisateur confirme.

    - 404 : conversation inconnue
    - 409 : action impossible à ce point de la conversation (par exemple un second ticket)
    """
    clf = _classifier()
    try:
        result = clf.discuter(request.conversation_id, request.action, request.text, request.categorie,
                              request.etapes_faites)
    except ConversationInconnue:
        raise HTTPException(status_code=404, detail="Conversation introuvable") from None
    except ActionRefusee as refus:
        raise HTTPException(status_code=409, detail=str(refus)) from None
    except Exception:
        logger.exception("Erreur dans /chat")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur") from None
    logger.info("chat %s tour %d: %s -> %s", result["conversation_id"], result["tour"], request.action, result["code"])
    return result


@app.post("/feedback", response_model=Feedback, status_code=201, summary="Avis sur une réponse (utile ou pas)")
async def feedback(request: FeedbackRequest) -> dict:
    """Enregistre l'avis de l'utilisateur sur un tour de la conversation (404 si le tour n'existe pas)."""
    conversation = stockage.lire("conversations", request.conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    try:
        return suivi.ajouter_avis(conversation, request.tour, request.utile, request.commentaire)
    except KeyError:
        raise HTTPException(status_code=404, detail="Tour introuvable dans cette conversation") from None


@app.get("/stats", response_model=StatsResponse, summary="Statistiques de l'agent")
async def stats() -> dict:
    """Taux de résolution sans ticket, catégories fréquentes, tickets par statut, avis."""
    return suivi.statistiques()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")
