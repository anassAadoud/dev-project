"""L'onglet « A file of tickets » (TP5, revu au TP5.2) : lire un CSV, classer chaque ticket, rendre le résultat.

Tout ce qui ne dépend pas de Streamlit est ici, et testé (tests/test_fichier.py) :
- lire()       un CSV venu d'Excel ou d'un outil de tickets : UTF-8 (avec ou sans BOM) ou Latin-1, séparateur
               virgule ou point-virgule, colonne « text » sans tenir compte de la casse, lignes vides ignorées,
               au plus MAX_LIGNES tickets ;
- resultats()  une ligne par ticket : catégorie, confiance, priorité, décision et sa raison, équipe, qui a décidé,
               l'article proposé, ses étapes, et si le cas est critique ;
- en_csv()     le fichier à télécharger, en UTF-8 avec BOM (Excel l'ouvre avec les accents).
Les cas critiques (sécurité, panne générale) sont montrés à part : la page propose leurs tickets tout de suite,
et ne les crée qu'après confirmation (règle des tickets du TP5.1).
"""
import io
from dataclasses import dataclass

import pandas as pd

from ui import client

MAX_LIGNES = 2000
MAX_OCTETS = 5 * 1024 * 1024  # 5 Mo : au-delà, la page refuse le fichier
ENCODAGES = ["utf-8-sig", "cp1252", "latin-1"]
COLONNES = ["category", "confidence", "priority", "decision", "reason", "team", "decided by", "article", "steps",
            "critical"]


@dataclass
class Lecture:
    """Le fichier lu, ou la raison pour laquelle il ne l'est pas."""

    tickets: pd.DataFrame | None
    colonne: str | None = None
    erreur: str | None = None
    avertissement: str | None = None


def lire(octets: bytes) -> Lecture:
    """Les tickets d'un CSV ; une erreur lisible si le fichier ne convient pas."""
    if len(octets) > MAX_OCTETS:
        return Lecture(None, erreur=f"The file is too large (more than {MAX_OCTETS // (1024 * 1024)} MB).")
    texte = None
    for encodage in ENCODAGES:
        try:
            texte = octets.decode(encodage)
            break
        except UnicodeDecodeError:
            continue
    if texte is None or not texte.strip():
        return Lecture(None, erreur="The file is empty.")
    lignes = texte.splitlines()
    entete = lignes[0]  # le séparateur se lit sur l'en-tête : les textes, eux, contiennent des virgules
    if not any(c in entete for c in ",;\t"):
        # Une seule colonne : chaque ligne est un ticket, virgules comprises (« Outlook crashes, then Teams too »).
        tickets = pd.DataFrame({entete.strip(): [ligne.strip().strip('"') for ligne in lignes[1:]]})
    else:
        separateur = max([",", ";", "\t"], key=entete.count)
        try:
            tickets = pd.read_csv(io.StringIO(texte), sep=separateur, dtype=str, keep_default_na=False)
        except (pd.errors.ParserError, pd.errors.EmptyDataError):
            return Lecture(None, erreur="The file is not a valid CSV file.")
    colonne = next((c for c in tickets.columns if str(c).strip().lower() == "text"), None)
    if colonne is None:
        return Lecture(None, erreur="No text column in the file: name the column of the ticket texts « text ».")
    tickets = tickets[tickets[colonne].str.strip() != ""].reset_index(drop=True)
    if tickets.empty:
        return Lecture(None, erreur="The text column is empty.")
    avertissement = None
    if len(tickets) > MAX_LIGNES:
        avertissement = f"Only the first {MAX_LIGNES} tickets of {len(tickets)} are processed."
        tickets = tickets.head(MAX_LIGNES)
    return Lecture(tickets, colonne=colonne, avertissement=avertissement)


def resultats(tickets: pd.DataFrame, reponses: list[client.Reponse]) -> pd.DataFrame:
    """Le fichier d'origine, et les colonnes de l'agent pour chaque ticket."""
    sortie = tickets.drop(columns=[c for c in COLONNES if c in tickets.columns]).copy()
    lignes = []
    for r in reponses:
        if not r.ok:
            lignes.append({"category": r.message, "confidence": None, "priority": None, "decision": None,
                           "reason": None, "team": None, "decided by": None, "article": None, "steps": None,
                           "critical": None})
            continue
        article = r.article
        lignes.append({
            "category": client.VERDICTS[r.label or "INDETERMINE"], "confidence": r.score, "priority": r.priorite,
            "decision": r.decision, "reason": client.MOTIFS.get(r.motif or "", ""), "team": r.groupe,
            "decided by": client.SOURCES.get(r.corps.get("source", ""), ""),
            "article": f"{article['id']} {article['titre']}" if article else "",
            "steps": " | ".join(article["etapes"]) if article else "",
            "critical": "yes" if r.motif == "critique" else "no",
        })
    return pd.concat([sortie.reset_index(drop=True), pd.DataFrame(lignes, columns=COLONNES)], axis=1)


def critiques(table: pd.DataFrame) -> pd.DataFrame:
    """Les tickets critiques (sécurité, panne générale) : leur ticket est proposé tout de suite."""
    return table[table["critical"] == "yes"]


def en_csv(table: pd.DataFrame) -> bytes:
    return table.to_csv(index=False).encode("utf-8-sig")
