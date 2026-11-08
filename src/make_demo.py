#!/usr/bin/env python
"""Génère un jeu de démonstration d'incidents informatiques en anglais, déterministe.

805 incidents, 115 par catégorie IT (securite, reseau, materiel, compte_acces,
facturation, logiciel, panne_service) :
  - 100 incidents nets par catégorie, écrits comme un utilisateur les écrit ;
  - 15 incidents mêlés par catégorie : un symptôme d'une autre catégorie d'abord,
    un retournement (« but the real problem is that »), puis le vrai problème, celui
    qui donne l'étiquette. Comme les avis mitigés de sentiment-app, ils sont volontaires :
    un sac de mots y voit deux symptômes de même poids et ne sait pas lequel conclut.
Chaque incident a aussi une priorité (low, medium, high), qui suit les mots
d'urgence ou de gêne de la phrase, pour entraîner le second modèle.

TP5.1 : les symptômes viennent aussi de la base de connaissances (titre et symptômes de chaque
article). Au TP5, 36 symptômes seulement donnaient un vocabulaire de 661 mots, et le modèle
hésitait sur 63 % d'un fichier de 1 000 tickets réels. La base et le modèle parlent maintenant
le même vocabulaire, et un article ajouté à la base enrichit aussi le jeu de démonstration.

Usage : python src/make_demo.py
Produit : data/demo_incidents.csv
"""
import csv
import random
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "demo_incidents.csv"
BASE = RACINE / "data" / "base_connaissances.csv"
GRAINE = 42
CATEGORIES = ["securite", "reseau", "materiel", "compte_acces", "facturation", "logiciel", "panne_service"]
NETS, MELES = 100, 15

# Le cœur de chaque incident : ce qui ne marche plus, en mots d'utilisateur.
SYMPTOMES = {
    "securite": [
        "I received a phishing email asking for my password",
        "the antivirus detected malware on my laptop",
        "someone logged into my account from an unknown country",
        "a ransomware message appeared and my files are encrypted",
        "a suspicious attachment was opened by a colleague",
        "the firewall reports repeated intrusion attempts on our server",
    ],
    "reseau": [
        "the VPN keeps disconnecting",
        "the Wi-Fi is very slow and drops every few minutes",
        "I cannot reach the intranet, DNS lookup fails",
        "there is no network connection on my desktop",
        "the remote desktop connection times out",
        "the office router restarts and the network is unstable",
    ],
    "materiel": [
        "the printer shows offline and nothing prints",
        "my laptop battery drains in less than an hour",
        "the second monitor stays black on the docking station",
        "several keys on my keyboard no longer respond",
        "the laptop fan is very loud and the machine overheats",
        "the scanner jams on every page",
    ],
    "compte_acces": [
        "my account is locked after too many password attempts",
        "I get permission denied on the shared drive",
        "the password reset link does not work",
        "the new employee has no access to the CRM yet",
        "two-factor authentication codes are always rejected",
        "I cannot log in to the HR portal with my credentials",
    ],
    "facturation": [
        "I was charged twice for the subscription",
        "the invoice shows the wrong amount for our licences",
        "our card payment was declined",
        "we need a refund for a cancelled licence",
        "the monthly bill includes a service we never ordered",
        "the payment receipt was never sent",
    ],
    "logiciel": [
        "the application crashes on startup after the update",
        "Outlook stopped receiving emails",
        "Excel freezes when I open a file with macros",
        "the accounting software shows an error code on export",
        "the browser extension stopped working after the upgrade",
        "the installer fails with an unknown error",
    ],
    "panne_service": [
        "the production database server is down",
        "the company website returns a 500 error for every customer",
        "the email service is unavailable for the whole office",
        "the ticketing portal is still down after the maintenance",
        "the file server is unreachable for all departments",
        "the payment platform is out of service",
    ],
}

# Le retournement des incidents mêlés : ce qui suit est le vrai problème.
RETOURNEMENTS = ["but the real problem is that", "that was fixed, however now", "then it got worse and",
                 "yet what really blocks me is that", "and now"]

# Priorité : les mots d'urgence ou de gêne de la phrase donnent l'étiquette.
URGENT = ["urgent, the whole team is blocked", "nobody can work, please fix it now", "critical for today's deadline"]
MOYEN = ["it happens every day", "please have a look today", "it slows down my work"]
FAIBLE = ["no rush, it is just annoying", "only sometimes, not blocking", "when you have time"]
DEBUTS = ["", "", "Hello, ", "Hi team, ", "Good morning, ", "Please help: ", "Could you investigate? ",
          "IT support request: "]


def symptomes_de_la_base() -> dict[str, list[str]]:
    """Le titre et chaque symptôme des articles de la base, rangés par catégorie (TP5.1)."""
    trouves: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    if not BASE.exists():
        return trouves
    with BASE.open(encoding="utf-8", newline="") as f:
        for article in csv.DictReader(f):
            if article["categorie"] in trouves:
                morceaux = [article["titre"], *article["symptomes"].split(";")]
                trouves[article["categorie"]] += [m.strip()[0].lower() + m.strip()[1:] for m in morceaux if m.strip()]
    return trouves


def tous_les_symptomes() -> dict[str, list[str]]:
    """Les symptômes écrits ici, puis ceux de la base, sans doublon."""
    base = symptomes_de_la_base()
    return {c: list(dict.fromkeys([*SYMPTOMES[c], *base[c]])) for c in CATEGORIES}


def phrase(symptome: str, contexte: str, priorite: str, rng: random.Random) -> str:
    suite = rng.choice({"high": URGENT, "medium": MOYEN, "low": FAIBLE}[priorite])
    debut = rng.choice(DEBUTS)
    corps = f"{contexte}, {symptome}" if contexte else symptome
    texte = f"{debut}{corps}, {suite}."
    return texte[0].upper() + texte[1:]


def incidents(categorie: str, rng: random.Random, symptomes: dict[str, list[str]]) -> list[tuple[str, str, str]]:
    lignes = []
    autres = [c for c in CATEGORIES if c != categorie]
    propres = symptomes[categorie]
    for i in range(NETS + MELES):
        priorite = ["high", "medium", "low"][i % 3]
        contexte = ""
        if i >= NETS:  # incident mêlé : d'abord le symptôme d'une autre catégorie, puis le retournement
            contexte = f"{rng.choice(symptomes[rng.choice(autres)])}, {rng.choice(RETOURNEMENTS)}"
        # Chaque symptôme sert au moins une fois, puis au hasard.
        symptome = propres[i] if i < min(len(propres), NETS) else rng.choice(propres)
        lignes.append((phrase(symptome, contexte, priorite, rng), categorie, priorite))
    return lignes


def main() -> int:
    rng = random.Random(GRAINE)
    symptomes = tous_les_symptomes()
    lignes = [ligne for categorie in CATEGORIES for ligne in incidents(categorie, rng, symptomes)]
    rng.shuffle(lignes)
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["text", "categorie", "priorite"])
        w.writerows(lignes)
    par_categorie = Counter(c for _, c, _ in lignes)
    par_priorite = Counter(p for _, _, p in lignes)
    print(f"{len(lignes)} incidents écrits dans {SORTIE.relative_to(RACINE).as_posix()}")
    print("  par catégorie : " + ", ".join(f"{c} {par_categorie[c]}" for c in CATEGORIES))
    print("  par priorité  : " + ", ".join(f"{p} {par_priorite[p]}" for p in ["high", "medium", "low"]))
    print(f"  dont {MELES * len(CATEGORIES)} incidents mêlés, volontairement difficiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
