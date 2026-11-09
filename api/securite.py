"""Sécurité et fiabilité de l'API (TP5.2, phase 6).

- LimiteCorps   : un corps de requête de plus de MAX_CORPS octets est refusé (413) dès que la limite est passée,
                  qu'il soit annoncé (Content-Length) ou envoyé par morceaux ; le plus gros corps légitime (/chat :
                  2 000 caractères et 20 étapes cochées de 500, accents échappés par JSON) fait 72 Ko.
- EnTetes       : en-têtes de sécurité sur chaque réponse (pas de devinette du type, pas d'affichage dans un
                  cadre, pas de référent, pas de cache : les réponses contiennent des incidents d'employés).
- refus_422     : la liste d'erreurs standard (loc, msg, type) sans l'entrée envoyée (« input »), ni le
                  contexte interne de Pydantic : un refus ne renvoie jamais le texte reçu.
- panne_500     : toute exception imprévue est journalisée côté serveur ; le client ne reçoit que
                  « Erreur interne du serveur », jamais une trace ni un chemin de fichier.
- origines()    : les sites autorisés par CORS, lus dans SUPPORT_ORIGINES ; par défaut la page Streamlit locale.
- identifiants  : les formats CNV-XXXXXXXX et TCK-XXXXXXXX ; un identifiant mal formé est traité comme
                  inconnu (404), sans lire le stockage.
"""
import logging
import os
import re

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("support_api")

MAX_CORPS = 128 * 1024
ORIGINES_PAR_DEFAUT = "http://localhost:8501,http://127.0.0.1:8501"
CONVERSATION = re.compile(r"CNV-[0-9A-F]{8}")
TICKET = re.compile(r"TCK-[0-9A-F]{8}")
EN_TETES = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cache-control", b"no-store"),
]


def origines() -> list[str]:
    valeur = os.environ.get("SUPPORT_ORIGINES", ORIGINES_PAR_DEFAUT)
    return [o.strip() for o in valeur.split(",") if o.strip()]


def conversation_valide(identifiant: str | None) -> bool:
    return identifiant is not None and CONVERSATION.fullmatch(identifiant) is not None


def ticket_valide(identifiant: str) -> bool:
    return TICKET.fullmatch(identifiant) is not None


async def _envoyer_413(send) -> None:
    corps = b'{"detail":"Requete trop grosse"}'
    await send({"type": "http.response.start", "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(corps)).encode())]})
    await send({"type": "http.response.body", "body": corps})


class LimiteCorps:
    """Middleware ASGI : refuse les corps trop gros, annoncés (Content-Length) ou envoyés par morceaux."""

    def __init__(self, app, maximum: int = MAX_CORPS) -> None:
        self.app, self.maximum = app, maximum

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        longueur = dict(scope.get("headers") or []).get(b"content-length")
        if longueur is not None and (not longueur.isdigit() or int(longueur) > self.maximum):
            await _envoyer_413(send)
            return
        # Le corps est lu ici, morceau par morceau, jusqu'à la limite ; puis rejoué à l'application.
        morceaux, recu = [], 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break  # le client s'est déconnecté
            morceaux.append(message.get("body", b""))
            recu += len(morceaux[-1])
            if recu > self.maximum:
                await _envoyer_413(send)
                return
            if not message.get("more_body", False):
                break
        corps, rejoue = b"".join(morceaux), False

        async def lire():
            nonlocal rejoue
            if not rejoue:
                rejoue = True
                return {"type": "http.request", "body": corps, "more_body": False}
            return await receive()

        await self.app(scope, lire, send)


class EnTetes:
    """Middleware ASGI : ajoute les en-têtes de sécurité à chaque réponse."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def envoyer(message):
            if message["type"] == "http.response.start":
                deja = {nom.lower() for nom, _ in message.get("headers", [])}
                message["headers"] = [*message.get("headers", []), *[(n, v) for n, v in EN_TETES if n not in deja]]
            await send(message)

        await self.app(scope, receive, envoyer)


async def refus_422(request: Request, erreur: RequestValidationError) -> JSONResponse:
    detail = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")}
              for e in erreur.errors()]
    return JSONResponse(status_code=422, content={"detail": detail})


async def panne_500(request: Request, erreur: Exception) -> JSONResponse:
    logger.exception("Erreur imprévue sur %s %s", request.method, request.url.path, exc_info=erreur)
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur"})
