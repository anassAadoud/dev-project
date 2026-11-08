"""Reformulation par un LLM local (Ollama), en option, désactivée par défaut (TP5.1).

L'agent marche sans LLM : la réponse vient toujours d'un article de la base. Si
SUPPORT_LLM=ollama, l'API demande en plus à Ollama de reformuler l'article trouvé pour
l'incident de l'utilisateur, sans rien inventer d'autre. La moindre erreur (Ollama absent,
trop lent, réponse vide) rend None : la page affiche alors l'article seul. Les tests ne
dépendent jamais d'Ollama : ils simulent sa réponse.

Variables : SUPPORT_LLM (vide = désactivé, « ollama » = activé), SUPPORT_LLM_MODELE
(llama3.2 par défaut), OLLAMA_URL (http://127.0.0.1:11434 par défaut).
"""
import logging
import os

import httpx

logger = logging.getLogger("support_api")
DELAI = 30.0

CONSIGNE = (
    "You are an IT support agent. Rewrite the knowledge base article below as a short, friendly answer "
    "to the user's incident, in English. Keep every step, in the same order, and do not add any step, "
    "command or fact that is not in the article.\n\nUser incident: {incident}\n\nArticle: {titre}\nSteps:\n{etapes}\n"
)


def active() -> bool:
    return os.environ.get("SUPPORT_LLM", "").strip().lower() == "ollama"


def modele() -> str:
    return os.environ.get("SUPPORT_LLM_MODELE", "llama3.2")


def description() -> str:
    """Pour /health : « off », ou le modèle Ollama utilisé."""
    return f"ollama ({modele()})" if active() else "off"


def reformuler(incident: str, article: dict | None) -> str | None:
    """La réponse reformulée, ou None (option désactivée, pas d'article, ou Ollama en panne)."""
    if not active() or article is None:
        return None
    etapes = "\n".join(f"{i}. {e}" for i, e in enumerate(article["etapes"], start=1))
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        r = httpx.post(f"{url}/api/generate", timeout=DELAI, json={
            "model": modele(), "stream": False,
            "prompt": CONSIGNE.format(incident=incident, titre=article["titre"], etapes=etapes)})
        r.raise_for_status()
        texte = str(r.json().get("response", "")).strip()
    except (httpx.HTTPError, ValueError):
        logger.warning("Ollama indisponible : la réponse reste l'article seul")
        return None
    return texte or None
