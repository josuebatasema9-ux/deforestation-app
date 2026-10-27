"""
page_accueil.py
---------------
Rôle : afficher l'onglet "Accueil / Home" :
  - description de l'application,
  - objectifs,
  - organisation (structure) de l'application,
  - flux de travail (de la donnée au rapport),
  - sources de données et méthodes,
  - guide de démarrage rapide, limites et informations utiles.

Pour modifier un texte : changez-le ici, dans le dictionnaire CONTENU
(une version "fr" et une version "en", avec les mêmes clés).
"""

import streamlit as st

CONTENU = {
    "fr": {
        "titre": "Bienvenue sur DeforestAlert",
        "intro": (
            "DeforestAlert est une application web de **détection automatique de la "
            "déforestation** à partir d'images satellitaires optiques (Landsat 8/9, "
            "Sentinel-2) et radar (Sentinel-1). Elle guide l'utilisateur depuis le "
            "chargement de la zone d'étude jusqu'à la production d'un rapport final."
        ),
        "titre_description": "📖 Description",
        "description": (
            "L'application combine l'imagerie optique et l'imagerie radar (SAR) pour "
            "suivre l'évolution du couvert forestier, y compris dans les régions "
            "souvent nuageuses. Les images sont prétraitées, assemblées (stacking), "
            "classées par un algorithme Random Forest, puis comparées à une date de "
            "référence pour repérer les pertes de couverture forestière."
        ),
        "titre_objectifs": "🎯 Objectifs",
        "objectifs": [
            "Détecter et cartographier les pertes de couverture forestière sur une zone d'étude définie par l'utilisateur.",
            "Automatiser la chaîne de traitement : acquisition, prétraitement, classification, détection de changement.",
            "Localiser les points chauds de déforestation (coordonnées, superficie) et les classer par type.",
            "Produire des livrables prêts à l'emploi : cartes, polygones, tableaux, graphiques et rapport interprété.",
        ],
        "titre_organisation": "🗂️ Organisation de l'application",
        "organisation": [
            ("🏠 Accueil", "Présentation, objectifs, organisation et guide d'utilisation."),
            ("⚙️ Traitement", "Quatre sous-étapes : Données et prétraitement ; Caractérisation spectrale et étiquetage des classes ; Classification ; Alerte de déforestation."),
            ("📊 Tableau de bord et rapport", "Synthèse des résultats clés (carte, points chauds, polygones, typologie, graphiques) et téléchargement des livrables."),
        ],
        "titre_flux": "🔄 Flux de travail",
        "flux": [
            ("1. Données et prétraitement", "Import de la zone d'étude (shapefile zippé), choix des capteurs, des dates, des bandes et des indices ; correction des nuages, ombres, vides, speckle ; stacking."),
            ("2. Caractérisation spectrale", "Import des points d'entraînement (shapefile ou Excel), extraction des valeurs spectrales par classe, étiquetage selon des seuils tirés de la littérature."),
            ("3. Classification", "Entraînement du Random Forest, carte d'occupation du sol, détection de changement et matrice de transition par rapport à l'année précédente ou à une baseline de référence."),
            ("4. Alerte de déforestation", "Extraction des points chauds de perte forestière : coordonnées, superficie, typologie."),
            ("5. Tableau de bord et rapport", "Visualisation des résultats et export d'un fichier ZIP (polygones, CSV, raster final, rapport Word)."),
        ],
        "titre_donnees": "🛰️ Données et méthodes",
        "donnees": [
            "**Optique** : Landsat 8/9 et Sentinel-2.",
            "**Radar (SAR)** : Sentinel-1.",
            "**Indices spectraux** : choisis par l'utilisateur selon son besoin (par exemple NDVI).",
            "**Classification** : Random Forest appliqué aux données stackées.",
            "**Détection de changement** : comparaison avec la dernière classification réalisée ou avec une baseline de référence.",
        ],
        "titre_guide": "🚀 Démarrage rapide",
        "guide": [
            "Ouvrez l'onglet **Traitement** et commencez par *Données et prétraitement*.",
            "Importez votre zone d'étude, choisissez capteurs, dates, bandes et indices.",
            "Appliquez les prétraitements, puis lancez le stacking.",
            "Importez vos points d'entraînement, puis lancez la classification.",
            "Lancez la détection de la déforestation.",
            "Consultez le **Tableau de bord** et téléchargez les résultats.",
        ],
        "titre_etat": "🧭 État d'avancement",
        "etat": (
            "L'application est en cours de construction. Pour l'instant, la connexion, "
            "le choix du thème et de la langue, et la structure des onglets sont "
            "opérationnels. Les modules de traitement seront ajoutés progressivement."
        ),
        "titre_limites": "⚠️ Bon à savoir",
        "limites": [
            "La qualité des résultats dépend de la qualité et du nombre des points d'entraînement.",
            "Une validation sur le terrain ou avec des images de haute résolution est recommandée avant toute décision.",
            "Les résultats d'alerte sont des détections automatiques : ils doivent être interprétés par un spécialiste.",
        ],
        "version": "Version 0.1 (prototype)",
    },
    "en": {
        "titre": "Welcome to DeforestAlert",
        "intro": (
            "DeforestAlert is a web application for **automatic deforestation "
            "detection** from optical (Landsat 8/9, Sentinel-2) and radar "
            "(Sentinel-1) satellite imagery. It guides the user from loading the "
            "study area to producing a final report."
        ),
        "titre_description": "📖 Description",
        "description": (
            "The application combines optical and radar (SAR) imagery to monitor "
            "forest cover change, including in frequently cloudy regions. Images are "
            "preprocessed, stacked, classified with a Random Forest algorithm, then "
            "compared with a reference date to identify forest cover loss."
        ),
        "titre_objectifs": "🎯 Objectives",
        "objectifs": [
            "Detect and map forest cover loss over a study area defined by the user.",
            "Automate the processing chain: acquisition, preprocessing, classification, change detection.",
            "Locate deforestation hotspots (coordinates, area) and classify them by type.",
            "Produce ready-to-use outputs: maps, polygons, tables, charts and an interpreted report.",
        ],
        "titre_organisation": "🗂️ Application structure",
        "organisation": [
            ("🏠 Home", "Overview, objectives, structure and user guide."),
            ("⚙️ Processing", "Four sub-steps: Data and preprocessing; Spectral characterization and class labeling; Classification; Deforestation alert."),
            ("📊 Dashboard & Report", "Summary of key results (map, hotspots, polygons, typology, charts) and download of the outputs."),
        ],
        "titre_flux": "🔄 Workflow",
        "flux": [
            ("1. Data and preprocessing", "Import the study area (zipped shapefile), choose sensors, dates, bands and indices; correct clouds, shadows, gaps, speckle; stacking."),
            ("2. Spectral characterization", "Import training points (shapefile or Excel), extract spectral values per class, label classes using thresholds from the literature."),
            ("3. Classification", "Random Forest training, land cover map, change detection and transition matrix against the previous year or a reference baseline."),
            ("4. Deforestation alert", "Extraction of forest loss hotspots: coordinates, area, typology."),
            ("5. Dashboard and report", "Results visualization and export of a ZIP file (polygons, CSV, final raster, Word report)."),
        ],
        "titre_donnees": "🛰️ Data and methods",
        "donnees": [
            "**Optical**: Landsat 8/9 and Sentinel-2.",
            "**Radar (SAR)**: Sentinel-1.",
            "**Spectral indices**: chosen by the user as needed (for example NDVI).",
            "**Classification**: Random Forest applied to the stacked data.",
            "**Change detection**: comparison with the last classification produced or with a reference baseline.",
        ],
        "titre_guide": "🚀 Quick start",
        "guide": [
            "Open the **Processing** tab and start with *Data and preprocessing*.",
            "Import your study area, choose sensors, dates, bands and indices.",
            "Apply preprocessing, then run the stacking.",
            "Import your training points, then run the classification.",
            "Run the deforestation detection.",
            "Open the **Dashboard** and download the results.",
        ],
        "titre_etat": "🧭 Development status",
        "etat": (
            "The application is under construction. For now, login, theme and "
            "language selection, and the tab structure are working. Processing "
            "modules will be added step by step."
        ),
        "titre_limites": "⚠️ Good to know",
        "limites": [
            "Result quality depends on the quality and number of training points.",
            "Field validation or high-resolution imagery is recommended before any decision.",
            "Alert results are automatic detections: they must be interpreted by a specialist.",
        ],
        "version": "Version 0.1 (prototype)",
    },
}


def afficher_accueil(langue):
    """Affiche le contenu de l'onglet Accueil dans la langue choisie."""
    c = CONTENU[langue]

    st.header(c["titre"])
    st.markdown(c["intro"])
    st.divider()

    # Description et objectifs côte à côte
    gauche, droite = st.columns(2)
    with gauche:
        st.subheader(c["titre_description"])
        st.markdown(c["description"])
    with droite:
        st.subheader(c["titre_objectifs"])
        for objectif in c["objectifs"]:
            st.markdown(f"- {objectif}")

    st.divider()

    # Organisation : une carte par onglet
    st.subheader(c["titre_organisation"])
    colonnes = st.columns(len(c["organisation"]))
    for colonne, (nom, texte) in zip(colonnes, c["organisation"]):
        with colonne:
            with st.container(border=True):
                st.markdown(f"**{nom}**")
                st.write(texte)

    st.divider()

    # Flux de travail : un bloc déroulant par étape
    st.subheader(c["titre_flux"])
    for nom, texte in c["flux"]:
        with st.expander(nom):
            st.write(texte)

    st.divider()

    # Données et guide de démarrage côte à côte
    gauche, droite = st.columns(2)
    with gauche:
        st.subheader(c["titre_donnees"])
        for ligne in c["donnees"]:
            st.markdown(f"- {ligne}")
    with droite:
        st.subheader(c["titre_guide"])
        for numero, ligne in enumerate(c["guide"], start=1):
            st.markdown(f"{numero}. {ligne}")

    st.divider()

    st.subheader(c["titre_etat"])
    st.info(c["etat"])

    st.subheader(c["titre_limites"])
    for ligne in c["limites"]:
        st.markdown(f"- {ligne}")

    st.caption(c["version"])
