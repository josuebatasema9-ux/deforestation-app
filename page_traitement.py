"""
page_traitement.py
------------------
Rôle : afficher l'onglet "Traitement / Processing".
Pour l'instant (étape 3) : un squelette qui liste les 4 sous-étapes.
À l'étape 4, ce fichier recevra la vraie mise en page :
  - zone de visualisation à gauche,
  - barre d'icônes étroite à droite (avec infobulles),
  - boutons de chaque sous-étape dans la barre supérieure.
"""

import streamlit as st

SOUS_ETAPES = {
    "fr": [
        ("📥", "Données et prétraitement"),
        ("🧪", "Caractérisation spectrale et étiquetage des classes"),
        ("🗺️", "Classification"),
        ("🚨", "Alerte de déforestation"),
    ],
    "en": [
        ("📥", "Data and preprocessing"),
        ("🧪", "Spectral characterization and class labeling"),
        ("🗺️", "Classification"),
        ("🚨", "Deforestation alert"),
    ],
}

TEXTES = {
    "fr": {
        "titre": "Traitement",
        "info": "Les sous-étapes ci-dessous seront activées une par une aux étapes suivantes.",
    },
    "en": {
        "titre": "Processing",
        "info": "The sub-steps below will be enabled one by one in the next steps.",
    },
}


def afficher_traitement(langue):
    """Affiche le squelette de l'onglet Traitement."""
    st.header(TEXTES[langue]["titre"])
    st.info(TEXTES[langue]["info"])

    colonnes = st.columns(len(SOUS_ETAPES[langue]))
    for colonne, (icone, nom) in zip(colonnes, SOUS_ETAPES[langue]):
        with colonne:
            with st.container(border=True):
                st.markdown(f"### {icone}")
                st.write(nom)
