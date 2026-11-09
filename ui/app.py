"""Interface Streamlit (TP5, conversation au TP5.1) : elle appelle l'API, jamais le modèle.

Lancer, API déjà démarrée dans un autre terminal : streamlit run ui/app.py
L'interface est en anglais (l'utilisateur et le modèle le sont) ; le code reste en français.

Quatre onglets : la conversation avec l'agent, le suivi d'un ticket, les statistiques, et le
tri d'un fichier de tickets (TP5). Streamlit relance le script à chaque clic : la conversation
(son identifiant et son fil) est gardée dans st.session_state.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # pour importer ui.client

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from ui import client  # noqa: E402

BLEU = "#2a78d6"  # la teinte unique du graphique des catégories (une seule série)
# Icônes Material de Streamlit (pas d'emojis) : une par catégorie, une pour l'agent.
ICONES = {"securite": ":material/shield:", "reseau": ":material/lan:", "materiel": ":material/computer:",
          "compte_acces": ":material/key:", "facturation": ":material/credit_card:", "logiciel": ":material/apps:",
          "panne_service": ":material/warning:", "INDETERMINE": ":material/help:"}
AGENT = ":material/support_agent:"
STYLE = """
<style>
  .bloc-etapes {border-left: 3px solid #2a78d6; padding: 0.2rem 0 0.2rem 0.8rem; margin: 0.4rem 0;}
  .pastille {display: inline-block; padding: 0.05rem 0.55rem; border-radius: 999px; font-size: 0.8rem;
             border: 1px solid rgba(127,127,127,0.4); margin-right: 0.3rem;}
  div[data-testid="stChatMessage"] {border-radius: 12px;}
</style>
"""

st.set_page_config(page_title="IT Support Agent", page_icon=AGENT)
st.markdown(STYLE, unsafe_allow_html=True)

session = client.creer_session()
etat = client.sante(session)
st.session_state.setdefault("fil", [])


def nouvelle_conversation() -> None:
    for cle in ["conv_id", "erreur", "avis"]:
        st.session_state.pop(cle, None)
    st.session_state["fil"] = []


def envoyer(action: str, dit: str, **champs) -> None:
    """Un tour : la phrase de l'utilisateur dans le fil, l'appel à /chat, la réponse de l'agent.
    Appelée par les boutons (on_click) avant que la page ne soit redessinée."""
    if action == "pas_resolu":
        champs["etapes_faites"] = etapes_cochees()
    reponse = client.discuter(session, action, st.session_state.get("conv_id"), **champs)
    if not reponse.ok:
        st.session_state["erreur"] = reponse.message
        return
    st.session_state.pop("erreur", None)
    st.session_state["conv_id"] = reponse.conversation_id
    st.session_state["fil"] += [{"role": "user", "texte": dit}, {"role": "assistant", "reponse": reponse}]
    if reponse.ticket:
        st.session_state["dernier_ticket"] = reponse.ticket["id"]


def derniere_reponse() -> client.Reponse | None:
    fil = st.session_state.get("fil") or []
    return fil[-1]["reponse"] if fil else None


def etapes_cochees() -> list[str]:
    """Les étapes de la dernière réponse que l'utilisateur a cochées."""
    r = derniere_reponse()
    if r is None or not r.article:
        return []
    return [etape for numero, etape in enumerate(r.article["etapes"], start=1)
            if st.session_state.get(f"etape-{r.conversation_id}-{r.tour}-{numero}")]


def soumettre() -> None:
    """Le message tapé : il continue la conversation, ou en commence une si la précédente est finie."""
    texte = st.session_state.get("saisie")
    if not texte:
        return
    r = derniere_reponse()
    if r is None or not r.choix:
        nouvelle_conversation()
    envoyer("message", texte, texte=texte)


def noter(r: client.Reponse, utile: bool) -> None:
    if client.donner_avis(session, r.conversation_id or "", r.tour or 0, utile).ok:
        st.session_state.setdefault("avis", {})[f"{r.conversation_id}-{r.tour}"] = utile


def libelle(categorie: str | None) -> str:
    return client.VERDICTS[categorie or "INDETERMINE"]


def afficher_reponse(r: client.Reponse, derniere: bool) -> None:
    """Le message de l'agent ; les étapes ne sont cochables que dans la dernière réponse."""
    st.markdown(r.message)
    categorie = r.corps.get("categorie")
    if categorie:
        st.markdown(f'<span class="pastille">{libelle(categorie)}</span>'
                    f'<span class="pastille">confidence {r.score:.0%}</span>'
                    f'<span class="pastille">priority {r.priorite}</span>', unsafe_allow_html=True)
    if r.corps.get("reformulation"):
        st.info(r.corps["reformulation"], icon=":material/lightbulb:")
    if r.article:
        st.markdown(f"**{r.article['titre']}** · <small>article {r.article['id']}</small>", unsafe_allow_html=True)
        st.markdown('<div class="bloc-etapes">', unsafe_allow_html=True)
        for numero, etape in enumerate(r.article["etapes"], start=1):
            if derniere:
                st.checkbox(f"{numero}. {etape}", key=f"etape-{r.conversation_id}-{r.tour}-{numero}")
            else:
                st.markdown(f"{numero}. {etape}")
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption(f"Ask for a technician if: {r.article['escalade_si']}")
    if r.corps.get("suggestions") and "choisir_article" in r.choix and derniere:
        titre = "Does one of these articles match your problem?" if not r.article else "Other articles that may help"
        st.caption(titre)
        for suggestion in r.corps["suggestions"]:
            st.button(f"{suggestion['titre']} ({libelle(suggestion.get('categorie'))})", icon=":material/article:",
                      key=f"sugg-{r.conversation_id}-{r.tour}-{suggestion['id']}", use_container_width=True,
                      on_click=envoyer, args=("choisir_article", f"Let's try: {suggestion['titre']}"),
                      kwargs={"article_id": suggestion["id"]})
    question = r.corps.get("question")
    if question and "diagnostic" in r.choix and derniere:
        st.caption(f"To find the right fix: **{question['question']}**")
        colonnes = st.columns(min(len(question["options"]), 3))
        for i, option in enumerate(question["options"]):
            colonnes[i % len(colonnes)].button(
                option["label"], key=f"diag-{r.conversation_id}-{r.tour}-{question['id']}-{option['id']}",
                use_container_width=True, on_click=envoyer, args=("diagnostic", option["label"]),
                kwargs={"question_id": question["id"], "option_id": option["id"]})
    if r.article and r.article.get("source"):
        st.caption(f"Source: {r.article['source']}")
    semblable = r.corps.get("ticket_semblable")
    if semblable:
        with st.expander(f"A similar past ticket was solved ({semblable['similarite']:.0%} similar)",
                         icon=":material/history:"):
            st.caption(f"{semblable['id']} · {semblable['source']}")
            st.markdown(f"> {semblable['text']}")
            st.markdown(f"**How it was solved:** {semblable['resolution']}")
    if r.ticket:
        st.success(f"Ticket **{r.ticket['id']}** created and sent to the **{r.ticket['groupe']}** team "
                   f"(status: {client.STATUTS[r.ticket['statut']]}).", icon=":material/confirmation_number:")
    cle = f"{r.conversation_id}-{r.tour}"
    if cle in st.session_state.get("avis", {}):
        st.caption("Thanks for your feedback!")
    else:
        haut, bas, _ = st.columns([2, 2, 5])
        for colonne, utile, texte, icone in [(haut, True, "Useful", ":material/thumb_up:"),
                                             (bas, False, "Not useful", ":material/thumb_down:")]:
            colonne.button(texte, icon=icone, key=f"avis-{cle}-{'haut' if utile else 'bas'}",
                           help="Was this answer useful?", on_click=noter, args=(r, utile))


def boutons(r: client.Reponse) -> None:
    """Les réponses possibles à la dernière question de l'agent (le champ choix de /chat)."""
    if "categorie" in r.choix:
        st.caption("What kind of problem is it?")
        colonnes = st.columns(4)
        for i, categorie in enumerate(r.categories):
            colonnes[i % 4].button(libelle(categorie), icon=ICONES[categorie], key=f"cat-{categorie}",
                                   use_container_width=True,
                                   on_click=envoyer, args=("categorie", f"It is about: {client.VERDICTS[categorie]}"),
                                   kwargs={"categorie": categorie})
    actions = [("confirmer_ticket", "Yes, create the ticket", ":material/confirmation_number:",
                "Yes, please create the ticket.", "primary"),
               ("refuser_ticket", "Not now", ":material/schedule:", "No ticket for now.", "secondary"),
               ("resolu", "Solved", ":material/check_circle:", "It's solved, thanks!", "primary"),
               ("pas_resolu", "Not solved", ":material/cancel:", "It's still not working.", "secondary"),
               ("demander_ticket", "Ask for a technician", ":material/contact_support:", "I'd like a technician.",
                "secondary")]
    visibles = [a for a in actions if a[0] in r.choix]
    if visibles:
        for colonne, (action, texte, icone, dit, genre) in zip(st.columns(len(visibles)), visibles, strict=True):
            colonne.button(texte, icon=icone, key=action, type=genre, use_container_width=True, on_click=envoyer,
                           args=(action, dit))


with st.sidebar:
    st.title(f"{AGENT} IT Support Agent")
    if etat.ok:
        st.caption(f"API ready: {etat.message}")
    else:
        st.error(etat.message)
    st.button("New conversation", icon=":material/add:", key="nouvelle", use_container_width=True,
              on_click=nouvelle_conversation)
    if st.session_state.get("conv_id"):
        st.caption(f"Conversation {st.session_state['conv_id']}")
    st.markdown("**How it works**\n\n1. Describe your problem.\n2. Try the suggested steps.\n"
                "3. Tell the agent if it is solved.\n\nA ticket is only created when the agent cannot solve it, "
                "when you ask for a technician, or for a critical case, and always after you confirm.")

onglet_chat, onglet_suivi, onglet_stats, onglet_lot = st.tabs(
    [":material/chat: Chat", ":material/confirmation_number: Track a ticket", ":material/bar_chart: Statistics",
     ":material/description: A file of tickets"])

with onglet_chat:
    fil = st.session_state["fil"]
    if not fil:
        with st.chat_message("assistant", avatar=AGENT):
            st.markdown("Hello! Describe your IT problem in English, and I will help you solve it step by step.")
    for i, entree in enumerate(fil):
        if entree["role"] == "user":
            with st.chat_message("user"):
                st.markdown(entree["texte"])
        else:
            with st.chat_message("assistant", avatar=AGENT):
                afficher_reponse(entree["reponse"], derniere=i == len(fil) - 1)
    derniere = derniere_reponse()
    if derniere is not None:
        boutons(derniere)
    if st.session_state.get("erreur"):
        (st.warning if st.session_state["erreur"] == client.REFUS else st.error)(st.session_state["erreur"])

    terminee = derniere is None or not derniere.choix
    invite = "Describe your incident in English…" if terminee else "Add a detail or answer the agent…"
    st.chat_input(invite, key="saisie", on_submit=soumettre)

with onglet_suivi:
    identifiant = st.text_input("Ticket ID", value=st.session_state.get("dernier_ticket", ""), key="suivi_id",
                                placeholder="TCK-1234ABCD")
    if st.button("Check the status", key="suivre") and identifiant.strip():
        st.session_state["suivi"] = client.suivre_ticket(session, identifiant)
    suivi: client.Reponse | None = st.session_state.get("suivi")
    if suivi is not None and not suivi.ok:
        st.warning(suivi.message)
    elif suivi is not None and suivi.ticket:
        t = suivi.ticket
        st.subheader(suivi.message)
        a, b, c = st.columns(3)
        a.metric("Team", t["groupe"])
        b.metric("Category", client.VERDICTS[t["label"]])
        c.metric("Priority", t["priorite"])
        if t.get("resume"):
            st.markdown(f"**Summary:** {t['resume']}")
        for essai in t.get("essais", []):
            st.caption(f"Already tried: {essai['titre']} ({essai['article_id']})")
        if t.get("resolution"):
            st.success(f"Resolution: {t['resolution']}")
        st.dataframe(pd.DataFrame([{"when": e["le"], "status": client.STATUTS[e["statut"]],
                                    "comment": e.get("commentaire") or ""} for e in t.get("historique", [])]),
                     hide_index=True, use_container_width=True)
        with st.expander("Technician: update this ticket"):
            statut = st.selectbox("Status", list(client.STATUTS), format_func=client.STATUTS.get, key="statut")
            commentaire = st.text_input("Comment", key="commentaire")
            resolution = st.text_area("Resolution (shown to users with a similar problem)", key="resolution")
            if st.button("Update the ticket", key="maj"):
                maj = client.mettre_a_jour_ticket(session, t["id"], statut, commentaire, resolution)
                st.session_state["suivi"] = client.suivre_ticket(session, t["id"]) if maj.ok else maj
                (st.success if maj.ok else st.warning)(maj.message)

with onglet_stats:
    stats = client.statistiques(session)
    if not stats.ok:
        st.warning(stats.message)
    else:
        s = stats.corps
        taux = s["taux_resolution_sans_ticket"]
        a, b, c, d = st.columns(4)
        a.metric("Solved without a ticket", "—" if taux is None else f"{taux:.0%}",
                 help="Finished conversations solved by the agent alone")
        b.metric("Conversations", s["conversations"], help=f"{s['en_cours']} still open")
        c.metric("Tickets", s["avec_ticket"])
        avis = s["avis_utiles"] + s["avis_pas_utiles"]
        d.metric("Useful answers", f"{s['avis_utiles']} of {avis}" if avis else "—",
                 help=f"{s['avis_pas_utiles']} answer(s) marked not useful")
        if s["categories"]:
            st.markdown("**Most frequent categories**")
            frequentes = pd.DataFrame({"category": [client.VERDICTS[k] for k in s["categories"]],
                                       "conversations": list(s["categories"].values())})
            st.bar_chart(frequentes, x="category", y="conversations", color=BLEU, horizontal=True)
            with st.expander("See the numbers"):
                st.dataframe(frequentes, hide_index=True, use_container_width=True)
        else:
            st.caption("No conversation yet.")
        if s["tickets_par_statut"]:
            st.caption("Tickets by status: " + ", ".join(f"{client.STATUTS[k]} {v}"
                                                         for k, v in s["tickets_par_statut"].items()))

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
            tickets["decided by"] = [client.SOURCES.get(r.corps.get("source", ""), "") for r in reponses]
            st.dataframe(tickets, use_container_width=True)
            st.write(client.resumer(reponses))
            st.write(f"{client.a_escalader(reponses)} of {len(reponses)} tickets go to a technician.")
            st.download_button("Download the results", tickets.to_csv(index=False),
                               file_name="results.csv", mime="text/csv")
