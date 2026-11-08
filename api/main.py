"""API REST de l'agent de support informatique (TP3).

Lancer : uvicorn api.main:app --reload
Doc    : http://localhost:8000/docs
"""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api import tickets
from api.model import GROUPES, Assistance, Prediction, SupportClassifier, load_model
from api.schemas import AssistResponse, HealthResponse, PredictRequest, PredictResponse, Ticket, TicketRequest

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
    description="Classe un incident informatique décrit en anglais, propose une solution de la base "
                "de connaissances, crée et escalade les tickets (modèle du TP2).",
    version="1.0.0",
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
    return {"status": "OK", "model": clf.model_name, "articles": clf.articles}


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


@app.get("/tickets/{identifiant}", response_model=Ticket, summary="Lire un ticket")
async def lire_ticket(identifiant: str) -> dict:
    """Renvoie le ticket, ou 404 s'il n'existe pas."""
    ticket = tickets.lire(identifiant)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    return ticket


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")
