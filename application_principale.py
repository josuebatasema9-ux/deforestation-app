"""
application_principale.py
-------------------------
Rôle : fichier principal de l'application. C'est lui qu'on lance avec
    streamlit run application_principale.py
Il affiche :
  - la page de connexion / création de compte (avec thème et langue),
  - puis, une fois connecté, les 3 onglets : Accueil, Traitement,
    Tableau de bord et rapport (provisoires pour l'instant).
"""

import re
import streamlit as st

from gestion_comptes_utilisateurs import (
    initialiser_base,
    creer_utilisateur,
    verifier_utilisateur,
)
from traductions_fr_en import traduire

# ---------- Configuration générale de la page ----------
st.set_page_config(page_title="DeforestAlert", page_icon="🌳", layout="wide")
initialiser_base()

# st.session_state = mémoire de la session (garde langue, thème, utilisateur)
memoire = st.session_state
memoire.setdefault("langue", "fr")
memoire.setdefault("theme", "claire")
memoire.setdefault("utilisateur", None)


# ---------- Barre du haut : boutons Thème et Langue ----------
def afficher_barre_theme_langue():
    _, colonne_theme, colonne_langue = st.columns([8, 1.4, 1.4])

    with colonne_langue:
        with st.popover(traduire(memoire.langue, "bouton_langue")):
            choix = st.radio(
                "langue",
                ["fr", "en"],
                index=["fr", "en"].index(memoire.langue),
                format_func=lambda x: "Français" if x == "fr" else "English",
                key="choix_langue",
                label_visibility="collapsed",
            )
            if choix != memoire.langue:
                memoire.langue = choix
                st.rerun()

    with colonne_theme:
        with st.popover(traduire(memoire.langue, "bouton_theme")):
            choix = st.radio(
                "theme",
                ["claire", "sombre"],
                index=["claire", "sombre"].index(memoire.theme),
                format_func=lambda x: traduire(memoire.langue, x),
                key="choix_theme",
                label_visibility="collapsed",
            )
            if choix != memoire.theme:
                memoire.theme = choix
                st.rerun()


def appliquer_theme():
    """Applique les couleurs claires ou sombres avec un peu de CSS."""
    if memoire.theme == "sombre":
        st.markdown(
            """<style>
            .stApp {background:#0e1117; color:#fafafa;}
            h1,h2,h3,p,label,span,li {color:#fafafa !important;}
            </style>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<style>
            .stApp {background:#ffffff; color:#111111;}
            </style>""",
            unsafe_allow_html=True,
        )


# ---------- Page de connexion ----------
def page_connexion():
    L = memoire.langue
    st.title("🌳 " + traduire(L, "titre"))
    _, centre, _ = st.columns([1, 2, 1])

    with centre:
        onglet_connexion, onglet_inscription = st.tabs(
            [traduire(L, "se_connecter"), traduire(L, "creer_compte")]
        )

        # --- Connexion ---
        with onglet_connexion:
            email = st.text_input(traduire(L, "email"), key="connexion_email")
            mdp = st.text_input(
                traduire(L, "mot_de_passe"), type="password", key="connexion_mdp"
            )
            if st.button(traduire(L, "se_connecter"), type="primary", key="bouton_connexion"):
                if verifier_utilisateur(email, mdp):
                    memoire.utilisateur = email.lower().strip()
                    st.rerun()
                else:
                    st.error(traduire(L, "erreur_connexion"))

        # --- Création de compte ---
        with onglet_inscription:
            email = st.text_input(traduire(L, "email"), key="inscription_email")
            mdp = st.text_input(
                traduire(L, "mot_de_passe"), type="password", key="inscription_mdp"
            )
            mdp2 = st.text_input(
                traduire(L, "confirmer"), type="password", key="inscription_mdp2"
            )
            if st.button(traduire(L, "creer_compte"), type="primary", key="bouton_inscription"):
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                    st.error(traduire(L, "erreur_email"))
                elif len(mdp) < 8:
                    st.error(traduire(L, "erreur_mdp_court"))
                elif mdp != mdp2:
                    st.error(traduire(L, "erreur_mdp_different"))
                elif creer_utilisateur(email, mdp):
                    st.success(traduire(L, "succes_compte"))
                else:
                    st.error(traduire(L, "erreur_existe"))


# ---------- Application après connexion (provisoire) ----------
def application_connectee():
    L = memoire.langue
    haut, bouton_sortie = st.columns([9, 1.6])
    haut.caption(f"👤 {memoire.utilisateur}")
    if bouton_sortie.button(traduire(L, "deconnexion")):
        memoire.utilisateur = None
        st.rerun()

    onglet_accueil, onglet_traitement, onglet_tableau = st.tabs(
        [traduire(L, "accueil"), traduire(L, "traitement"), traduire(L, "tableau_bord")]
    )
    with onglet_accueil:
        st.info(traduire(L, "a_construire"))
    with onglet_traitement:
        st.info(traduire(L, "a_construire"))
    with onglet_tableau:
        st.info(traduire(L, "a_construire"))


# ---------- Lancement ----------
appliquer_theme()
afficher_barre_theme_langue()

if memoire.utilisateur:
    application_connectee()
else:
    page_connexion()
