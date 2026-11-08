#!/usr/bin/env python
"""La priorité d'un incident, décidée à part de la catégorie (TP5.2).

Au TP5.1, la priorité venait d'un second modèle appris sur les mêmes phrases synthétiques que la
catégorie : 63 % de priorités exactes sur un fichier aux formules d'urgence nouvelles. La règle
de la priorité est pourtant connue et écrite (docs/semaine5.2.md) :

  1. un calme explicite, négations comprises (« not urgent », « no rush », « can wait »)  -> low
  2. une urgence explicite ou un impact sur l'activité (« ASAP », « whole team », « all customers »,
     « nobody can work », une échéance proche)                                               -> high
  3. sinon, la catégorie décide : panne générale ou sécurité -> high ; le reste -> medium

Le calme passe avant l'urgence : « nothing urgent » contient « urgent ». Le modèle appris reste un
repli, pour un texte sans indice dont la catégorie est inconnue. Les listes d'indices viennent du
vocabulaire courant du support, pas des jeux de mesure.

Usage : python src/priorite.py "the whole team is blocked, please fix it asap"
"""
import re
import sys

CALME = re.compile(
    r"\b(not|nothing|no|non)[\s-]+(urgent|critical|blocking|pressing|important)\b"
    r"|\bno (rush|hurry|stress|need to hurry|pressure)\b|\blow[\s-]priority\b|\bminor (issue|problem)\b"
    r"|\b(whenever|when) (you|u) (can|have (the )?time)\b|\bwhenever (possible|convenient)\b|\bcan wait\b"
    r"|\btake your time\b|\bnot a big deal\b|\bjust (letting you know|fyi|so you know)\b|\bfor (information|info)\b"
    r"|\bno impact\b|\bat your convenience\b|\bnext week is fine\b|\blater is fine\b",
    re.IGNORECASE)
URGENCE = re.compile(
    r"\burgent(ly)?\b|\basap\b|\bas soon as possible\b|\bemergency\b|\bcritical\b|\bimmediately\b|\bright (away|now)\b"
    r"|\btop priority\b|\bhigh[\s-]priority\b|\b(completely |totally )?(blocked|stuck)\b|\bblocking\b"
    r"|\b(can'?t|cannot|can not|unable to) work\b|\bdeadline\b|\bdue (today|tonight|in \w+)\b"
    r"|\bin (\d+|ten|five|twenty|thirty) (min|mins|minutes)\b|\bin (an|one|two|\d+) hours?\b"
    r"|\bbefore (my|the|our) (meeting|presentation|demo|call|deadline)\b|\b(client|customer) (call|meeting|demo)\b"
    r"|\b(whole|entire) (team|department|company|office|floor|organi[sz]ation|branch)\b"
    r"|\b(everyone|everybody|nobody|no one) (can|is|in)\b|\ball (users|employees|staff|customers|clients|branches)\b"
    r"|\b(customers|clients) (cannot|can'?t|are calling)\b|\bproduction\b|\blosing (money|sales|customers)\b"
    r"|\b\d+ (people|users|colleagues) (are )?(waiting|blocked)\b|\bpayroll\b|\baudit\b",
    re.IGNORECASE)
PAR_CATEGORIE = {"securite": "high", "panne_service": "high"}  # les autres catégories : medium
# Un incident qui touche tout le monde est une panne de service (pratique du support : incident majeur).
# Mesuré sur la validation (3 graines) : faux 5,3 -> 4,0 ; confirmé sur le jeu du TP5.1 : faux 6,0 -> 4,0.
IMPACT_GENERAL = re.compile(
    r"\b(whole|entire) (company|organi[sz]ation|office|department|branch|building)\b|\bcompany[\s-]wide\b"
    r"|\b(everyone|everybody|nobody|no one)\b"
    r"|\b(all|every) (users?|employees?|staff|departments?|branch(es)?|offices?|customers?|clients?|apps?|applications?)\b"
    r"|\bfor all\b|\bin all offices\b",
    re.IGNORECASE)


def impact_general(texte: str) -> bool:
    return bool(IMPACT_GENERAL.search(texte))


def indice(texte: str) -> str | None:
    """« low » pour un calme explicite, « high » pour une urgence ou un impact, None sans indice."""
    if CALME.search(texte):
        return "low"
    if URGENCE.search(texte):
        return "high"
    return None


def priorite(texte: str, categorie: str | None, repli: str | None = None) -> tuple[str, str]:
    """La priorité et sa raison : « indice » (le texte le dit), « categorie » (la règle par défaut),
    ou « modele » (repli quand la catégorie est inconnue)."""
    trouve = indice(texte)
    if trouve:
        return trouve, "indice"
    if categorie and categorie in {"securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel",
                                   "panne_service"}:
        return PAR_CATEGORIE.get(categorie, "medium"), "categorie"
    return (repli or "medium"), "modele"


if __name__ == "__main__":
    print(indice(" ".join(sys.argv[1:])) or "aucun indice")
