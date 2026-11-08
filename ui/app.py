"""Interface Streamlit (TP5) : elle appelle l'API, jamais le modèle.

Lancer, API déjà démarrée dans un autre terminal : streamlit run ui/app.py
L'interface est en anglais (l'utilisateur et le modèle le sont) ; le code reste en français.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # pour importer ui.client

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from ui import client  # noqa: E402

st.set_page_config(page_title="IT Support Agent")
st.title("IT Support Agent")

session = client.creer_session()
etat = client.sante(session)
if etat.ok:
    st.caption(f"API ready: {etat.message}")
else:
    st.error(etat.message)

onglet_incident, onglet_lot = st.tabs(["Report an incident", "A file of tickets"])

with onglet_incident:
    texte = st.text_area("Describe your incident (in English)", key="texte")
    if st.button("Get help", key="aider"):
        # Streamlit relance le script à chaque clic : la réponse est gardée dans st.session_state.
        st.session_state["aide"] = client.assister(session, texte)
        st.session_state["texte_aide"] = texte
        st.session_state.pop("ticket", None)

    aide: client.Reponse | None = st.session_state.get("aide")
    if aide is not None and not aide.ok:
        (st.warning if aide.message == client.REFUS else st.error)(aide.message)
    elif aide is not None:
        st.metric(client.VERDICTS[aide.label or "INDETERMINE"], f"{aide.score:.0%}")
        if aide.decision == "escalade":
            st.warning(aide.message)
        else:
            st.info(aide.message)

        if aide.article:
            st.subheader(aide.article["titre"])
            st.caption(f"Article {aide.article['id']} of the knowledge base")
            for numero, etape in enumerate(aide.article["etapes"], start=1):
                st.checkbox(f"{numero}. {etape}", key=f"etape-{numero}")
            st.caption(f"Ask for a technician if: {aide.article['escalade_si']}")

        if aide.decision == "solution":
            resolu = st.radio("Is it solved?", ["Yes", "No"], index=None, horizontal=True, key="resolu")
            if resolu == "Yes":
                st.success("Great, the incident is closed. No ticket was created.")
            elif resolu == "No" and "ticket" not in st.session_state:
                st.session_state["ticket"] = client.creer_ticket(
                    session, st.session_state["texte_aide"], aide,
                    raison=f"not solved after article {aide.article['id']}" if aide.article else "not solved")
        elif "ticket" not in st.session_state and st.button("Create the ticket", key="creer"):
            st.session_state["ticket"] = client.creer_ticket(session, st.session_state["texte_aide"], aide,
                                                             raison=aide.corps.get("raison", ""))

        ticket: client.Reponse | None = st.session_state.get("ticket")
        if ticket is not None:
            (st.success if ticket.ok else st.error)(ticket.message)

with onglet_lot:
    fichier = st.file_uploader("CSV file of tickets with a text column", type="csv")
    if fichier is not None:
        tickets = pd.read_csv(fichier)
        if "text" not in tickets.columns:
            st.error("No text column in the file.")
        else:
            reponses = client.assister_lot(session, tickets["text"].astype(str).tolist())
            tickets["category"] = [client.VERDICTS[r.label] if r.ok and r.label else r.message for r in reponses]
            tickets["confidence"] = [r.score for r in reponses]
            tickets["priority"] = [r.priorite for r in reponses]
            tickets["decision"] = [r.decision for r in reponses]
            tickets["team"] = [r.groupe for r in reponses]
            st.dataframe(tickets, use_container_width=True)
            st.write(client.resumer(reponses))
            st.write(f"{client.a_escalader(reponses)} of {len(reponses)} tickets go to a technician.")
            st.download_button("Download the results", tickets.to_csv(index=False),
                               file_name="results.csv", mime="text/csv")
