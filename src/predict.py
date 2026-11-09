#!/usr/bin/env python
"""Prédiction unitaire : la catégorie IT d'un incident, sa confiance, sa priorité (TP2, typé au TP4).

Usage :
  python src/predict.py "My VPN keeps disconnecting every 10 minutes"
  >>> from predict import predict ; predict("texte")
"""
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

import joblib
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

RACINE = Path(__file__).resolve().parents[1]
MODELE = RACINE / "models" / "support.joblib"


class Resultat(TypedDict):
    """Ce que renvoie predict() : l'étiquette du modèle, sa confiance, la priorité, et la part
    des mots du texte que le modèle connaît (le garde-fou de vocabulaire du TP4)."""

    label: str
    score: float
    priorite: str
    connus: float


@lru_cache(maxsize=1)
def charger_modele() -> Any:
    """Chargé une seule fois par processus, pas à chaque appel."""
    if not MODELE.exists():
        # Chemin complet, pas relatif au dépôt : le modèle peut se trouver ailleurs (TP4, test d'intégration).
        raise FileNotFoundError(f"modèle introuvable : {MODELE}. Lancez python src/train.py")
    return joblib.load(MODELE)


def vectoriseur_mots(pipeline: Any) -> Any:
    """Le vectoriseur de mots du modèle de catégorie, celui du garde-fou de vocabulaire.
    TP5.2 : le modèle peut assembler mots et caractères (FeatureUnion) ; le garde-fou ne lit que les mots,
    car presque toute suite de lettres a des n-grammes de caractères connus."""
    etape = pipeline.named_steps["tfidf"]
    return etape if hasattr(etape, "vocabulary_") else dict(etape.transformer_list)["mots"]


# TP5.2 : des mots qui ne disent rien de l'incident. Un message qui n'a qu'eux (« It does not work »,
# « it is broken, please help ») est trop vague pour être classé : l'agent pose une question.
GENERIQUES = frozenset({
    "work", "works", "working", "worked", "broken", "problem", "problems", "issue", "issues", "help", "error", "errors",
    "wrong", "fix", "fixed", "again", "thing", "things", "stuff", "please", "pls", "urgent", "today", "now", "still",
    "doesnt", "dont", "cant", "wont", "isnt", "hi", "hello", "hey", "thanks", "thank", "thx", "asap", "team",
    "support", "need", "want", "know", "ok", "okay", "anymore", "really", "weird", "strange", "since", "morning",
    "does", "did", "doing", "done", "get", "got", "getting", "keep", "keeps", "seems", "seem", "happen", "happens",
    "happened", "going", "anything", "something", "everything", "nothing", "guys", "sir", "madam", "dear",
    # les mots du temps disent quand, pas quoi (TP5.2)
    "week", "weeks", "day", "days", "yesterday", "tomorrow", "tonight", "hour", "hours", "minute", "minutes", "time",
    "times", "same", "usual", "like", "monday", "tuesday", "wednesday", "thursday", "friday", "weekend",
})


# TP5.2 : un message qui annonce son vrai problème après une première partie réglée ou hors de cause
# (« The printer was fixed, but my account is locked », « the issue is that… », « turns out… »).
# Mesuré sur 36 messages variés hors du jeu de démonstration (data/jeu_melanges.csv) : 74 % -> 82 % de
# catégories justes sur les messages mêlés, 98 % inchangé sur les pièges (« the VPN connects but… »).
PIVOT = re.compile(
    r"\b(the|my|our)\s+(real|actual|main)?\s*(problem|issue|cause)\s+is( that)?\b"
    r"|\bturns out( that)?( it was)?\b|\bwhat'?s really (broken|wrong) is\b|\bwhat really blocks me is( that)?\b"
    r"|\bactually\s+(the\s+)?(real\s+)?(problem|issue|cause)\s+is\b"
    r"|\b(fixed|fine|ok|okay|works( again)?|corrected|unlocked|updated|on my side|not the [\w-]+|not a [\w-]+ problem"
    r"|my mistake[^,]*)\s*(yesterday|now|this morning|earlier)?\s*[,;]\s*(but|however|actually|now|turns out)?\s*"
    r"(the real (issue|problem) is( that)?)?",
    re.IGNORECASE)


def partie_principale(texte: str) -> str:
    """La partie du message qui décrit le vrai problème (tout le texte s'il n'annonce rien)."""
    trouves = list(PIVOT.finditer(texte))
    if not trouves:
        return texte
    if not texte[:trouves[-1].start()].strip():  # « The issue is that my account… » : rien à retirer avant
        return texte
    reste = texte[trouves[-1].end():].strip(" ,;")
    return reste if len(reste.split()) >= 3 else texte


def est_vague(texte: str, vectoriseur: Any) -> bool:
    """Vrai si, hors mots vides, le texte n'a que des mots génériques (ou aucun mot)."""
    mots = [t for t in vectoriseur.build_analyzer()(texte) if " " not in t and t not in ENGLISH_STOP_WORDS]
    return not [m for m in mots if m not in GENERIQUES]


def part_connue(texte: str, vectoriseur: Any) -> float:
    """Part des mots du texte (unigrammes) présents dans le vocabulaire du modèle (notebook, section 15.1).

    TP5.1 : les mots vides anglais (the, is, on, our…) ne comptent plus. Ils sont connus de tout
    modèle et ne disent rien de l'incident : « Our coffee machine leaks water on the floor » passait
    le garde-fou avec 50 % de mots « connus », dont aucun ne parlait d'informatique."""
    mots = [t for t in vectoriseur.build_analyzer()(texte) if " " not in t and t not in ENGLISH_STOP_WORDS]
    return sum(t in vectoriseur.vocabulary_ for t in mots) / len(mots) if mots else 0.0


def predict(texte: str) -> Resultat:
    """Renvoie {'label': catégorie, 'score': confiance, 'priorite': ..., 'connus': part de mots connus}."""
    if not isinstance(texte, str) or not texte.strip():
        raise ValueError("texte vide")
    modeles = charger_modele()
    categorie = modeles["categorie"]
    probas = categorie.predict_proba([texte])[0]
    return {
        "label": str(categorie.classes_[probas.argmax()]),
        "score": round(float(probas.max()), 4),
        "priorite": str(modeles["priorite"].predict([texte])[0]),
        "connus": round(part_connue(texte, vectoriseur_mots(categorie)), 4),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    resultat = predict(" ".join(sys.argv[1:]))
    print(f"{resultat['label']} (confiance {resultat['score']:.0%}, priorité {resultat['priorite']}, "
          f"mots connus {resultat['connus']:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
