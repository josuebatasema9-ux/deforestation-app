"""
page_tableau_bord_rapport.py
----------------------------
Rôle : afficher l'onglet "Tableau de bord et rapport".
Pour l'instant (étape 3) : un squelette qui liste le contenu prévu.
À l'étape 8, ce fichier affichera la carte, les points chauds, les polygones,
la typologie, les graphiques et le bouton de téléchargement du ZIP.
"""

import streamlit as st

TEXTES = {
    "fr": {
        "titre": "Tableau de bord et rapport",
        "info": "Les résultats apparaîtront ici une fois la détection de la déforestation effectuée.",
        "contenu_prevu": "Contenu prévu",
        "elements": [
            "Carte des résultats",
            "Points chauds et coordonnées",
            "Polygones de déforestation et superficies",
            "Typologie de la déforestation et graphiques",
            "Téléchargement des résultats (ZIP : shapefile, CSV, raster final, rapport Word)",
        ],
    },
    "en": {
        "titre": "Dashboard & Report",
        "info": "Results will appear here once the deforestation detection has been run.",
        "contenu_prevu": "Planned content",
        "elements": [
            "Results map",
            "Hotspots and coordinates",
            "Deforestation polygons and areas",
            "Deforestation typology and charts",
            "Results download (ZIP: shapefile, CSV, final raster, Word report)",
        ],
    },
}


def afficher_tableau_bord(langue):
    """Affiche le squelette de l'onglet Tableau de bord et rapport."""
    t = TEXTES[langue]
    st.header(t["titre"])
    st.info(t["info"])
    st.subheader(t["contenu_prevu"])
    for element in t["elements"]:
        st.markdown(f"- {element}")
