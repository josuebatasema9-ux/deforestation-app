"""
page_traitement.py
------------------
Rôle : afficher l'onglet "Traitement / Processing" avec un écran divisé en deux :

  GAUCHE (large)  : le flux procédural de la sous-étape + la carte de visualisation
  DROITE (étroite): 4 icônes, une par sous-étape. Au survol, le nom apparaît.

Au-dessus, une BARRE D'OUTILS affiche les boutons propres à la sous-étape active.

État d'avancement :
  - Étape 4 : mise en page et navigation (terminé)
  - Étape 5a : import de la zone d'étude (shapefile .zip) + affichage + recentrage
  - Étape 5b : connexion Earth Engine, capteurs, bandes, indices, dates, recherche
    d'images avec aperçus (voir outils_donnees_satellitaires.py)
  - Étape 5c : prétraitements (nuages, vides, speckle...) et stacking, avec affichage
    de l'image finale (voir outils_pretraitement_stacking.py)
  - Les autres outils sont encore des emplacements (étapes 6 et 7).
"""

import folium
import streamlit as st
from streamlit_folium import st_folium

from lecture_zone_etude import lire_zone_etude, ErreurZoneEtude
from outils_donnees_satellitaires import (
    afficher_panneau_donnees,
    auto_connexion,
    outil_bandes,
    outil_capteurs,
    outil_dates,
    recherche_valide,
)
from outils_pretraitement_stacking import (
    afficher_panneau_pile,
    outil_pretraitement,
    outil_stacking,
    pile_valide,
    pretraitement_valide,
)

# --------------------------------------------------------------------------
# Description des 4 sous-étapes.
# Chaque outil = (identifiant, libellé FR, libellé EN).
# L'outil "zone" est le seul réellement actif pour l'instant.
# "etape_ou_dispo" : étape du projet où les autres outils deviendront actifs.
# --------------------------------------------------------------------------
SOUS_ETAPES = [
    {
        "id": "donnees",
        "icone": "📥",
        "etape_ou_dispo": 5,
        "nom": {"fr": "Données et prétraitement", "en": "Data and preprocessing"},
        "outils": [
            ("zone", "📁 Importer la zone (shp .zip)", "📁 Import area (zipped shp)"),
            ("capteurs", "🛰️ Capteurs et API", "🛰️ Sensors and API"),
            ("bandes", "🎚️ Bandes et indices", "🎚️ Bands and indices"),
            ("dates", "📅 Dates", "📅 Dates"),
            ("pretraitement", "🧹 Prétraitement", "🧹 Preprocessing"),
            ("stacking", "🧱 Stacking", "🧱 Stacking"),
        ],
        "flux": {
            "fr": ["Zone d'étude", "Données satellitaires", "Bandes et indices", "Prétraitement", "Stacking"],
            "en": ["Study area", "Satellite data", "Bands and indices", "Preprocessing", "Stacking"],
        },
    },
    {
        "id": "spectrale",
        "icone": "🧪",
        "etape_ou_dispo": 6,
        "nom": {"fr": "Caractérisation spectrale et étiquetage des classes",
                "en": "Spectral characterization and class labeling"},
        "outils": [
            ("points", "📁 Importer les points (shp / Excel)", "📁 Import points (shp / Excel)"),
            ("signatures", "📈 Signatures spectrales", "📈 Spectral signatures"),
            ("etiquetage", "🏷️ Étiqueter les classes", "🏷️ Label classes"),
        ],
        "flux": {
            "fr": ["Points d'entraînement", "Signatures spectrales", "Seuils (littérature)", "Étiquetage"],
            "en": ["Training points", "Spectral signatures", "Thresholds (literature)", "Labeling"],
        },
    },
    {
        "id": "classification",
        "icone": "🗺️",
        "etape_ou_dispo": 7,
        "nom": {"fr": "Classification", "en": "Classification"},
        "outils": [
            ("rf", "🌲 Classification (Random Forest)", "🌲 Classification (Random Forest)"),
            ("changement", "🔁 Détection de changement", "🔁 Change detection"),
            ("matrice", "🧮 Matrice de transition", "🧮 Transition matrix"),
        ],
        "flux": {
            "fr": ["Entraînement du modèle", "Carte d'occupation du sol", "Détection de changement", "Matrice de transition"],
            "en": ["Model training", "Land cover map", "Change detection", "Transition matrix"],
        },
    },
    {
        "id": "alerte",
        "icone": "🚨",
        "etape_ou_dispo": 7,
        "nom": {"fr": "Alerte de déforestation", "en": "Deforestation alert"},
        "outils": [
            ("chauds", "🔥 Points chauds de perte", "🔥 Loss hotspots"),
            ("coordonnees", "📐 Coordonnées et superficies", "📐 Coordinates and areas"),
            ("typologie", "🗂️ Typologie", "🗂️ Typology"),
        ],
        "flux": {
            "fr": ["Pertes forestières", "Points chauds", "Coordonnées et superficie", "Typologie"],
            "en": ["Forest loss", "Hotspots", "Coordinates and area", "Typology"],
        },
    },
]

TEXTES = {
    "fr": {
        "outils": "Outils",
        "flux": "Flux de traitement",
        "carte": "Visualisation",
        "bientot": "Cet outil sera activé à l'étape {n} du projet.",
        "satellite": "Satellite",
        "plan": "Plan",
        "attribution_esri": "Imagerie : Esri, Maxar, Earthstar Geographics",
        "couche_zone": "Zone d'étude",
        # --- import de la zone ---
        "zone_aide": "Envoyez un fichier .zip contenant votre shapefile (.shp, .shx, .dbf, .prj).",
        "zone_uploader": "Fichier .zip de la zone d'étude",
        "zone_chargee": "Zone d'étude chargée : {nom}",
        "zone_entites": "Polygones",
        "zone_superficie": "Superficie",
        "zone_crs": "Système d'origine",
        "zone_retirer": "🗑️ Retirer la zone",
        "zone_crs_suppose": "Le fichier .prj est absent : le système WGS84 (EPSG:4326) a été supposé.",
        "zone_lecture": "Lecture du shapefile…",
        "zone_aucune": "Aucune zone d'étude chargée. Utilisez « Importer la zone » dans la barre d'outils.",
        "erreurs": {
            "trop_gros": "Le fichier est trop volumineux (limite : 50 Mo compressé).",
            "zip_invalide": "Ce fichier n'est pas un .zip valide.",
            "pas_de_shp": "Aucun fichier .shp trouvé dans le .zip.",
            "fichiers_manquants": "Fichier .dbf manquant dans le .zip.",
            "lecture_impossible": "Le shapefile n'a pas pu être lu. Vérifiez qu'il n'est pas corrompu.",
            "pas_de_polygone": "Le shapefile ne contient aucun polygone (la zone d'étude doit être un polygone).",
            "crs_absent": "Le système de coordonnées est introuvable (.prj manquant). Ajoutez le fichier .prj au .zip.",
        },
    },
    "en": {
        "outils": "Tools",
        "flux": "Processing flow",
        "carte": "Visualization",
        "bientot": "This tool will be enabled at project step {n}.",
        "satellite": "Satellite",
        "plan": "Map",
        "attribution_esri": "Imagery: Esri, Maxar, Earthstar Geographics",
        "couche_zone": "Study area",
        # --- import de la zone ---
        "zone_aide": "Upload a .zip file containing your shapefile (.shp, .shx, .dbf, .prj).",
        "zone_uploader": "Study area .zip file",
        "zone_chargee": "Study area loaded: {nom}",
        "zone_entites": "Polygons",
        "zone_superficie": "Area",
        "zone_crs": "Original system",
        "zone_retirer": "🗑️ Remove area",
        "zone_crs_suppose": "The .prj file is missing: WGS84 (EPSG:4326) was assumed.",
        "zone_lecture": "Reading shapefile…",
        "zone_aucune": "No study area loaded. Use “Import area” in the toolbar.",
        "erreurs": {
            "trop_gros": "The file is too large (limit: 50 MB compressed).",
            "zip_invalide": "This is not a valid .zip file.",
            "pas_de_shp": "No .shp file found in the .zip.",
            "fichiers_manquants": "Missing .dbf file in the .zip.",
            "lecture_impossible": "The shapefile could not be read. Check that it is not corrupted.",
            "pas_de_polygone": "The shapefile contains no polygon (the study area must be a polygon).",
            "crs_absent": "Coordinate system not found (.prj missing). Add the .prj file to the .zip.",
        },
    },
}


# --------------------------------------------------------------------------
# Zone d'étude : import, retrait, résumé
# --------------------------------------------------------------------------
def _outil_importer_zone(langue):
    """Bouton déroulant (popover) pour envoyer le .zip de la zone d'étude."""
    t = TEXTES[langue]
    memoire = st.session_state
    libelle = [o for o in SOUS_ETAPES[0]["outils"] if o[0] == "zone"][0]
    libelle = libelle[1] if langue == "fr" else libelle[2]

    with st.popover(libelle, use_container_width=True):
        st.caption(t["zone_aide"])
        # La clé change à chaque retrait de zone : cela vide le champ d'envoi.
        fichier = st.file_uploader(
            t["zone_uploader"], type=["zip"],
            key=f"uploader_zone_{memoire.get('zone_uploader_n', 0)}",
            label_visibility="collapsed",
        )
        if fichier is not None:
            identifiant = (fichier.name, fichier.size)
            # On ne relit le fichier que s'il est nouveau (pas à chaque clic).
            if memoire.get("zone_fichier_id") != identifiant:
                with st.spinner(t["zone_lecture"]):
                    try:
                        resultat = lire_zone_etude(fichier.getvalue())
                    except ErreurZoneEtude as erreur:
                        memoire["zone_fichier_id"] = identifiant
                        memoire["zone"] = None
                        memoire["zone_erreur"] = erreur.code
                    else:
                        resultat["nom"] = fichier.name
                        memoire["zone_fichier_id"] = identifiant
                        memoire["zone"] = resultat
                        memoire["zone_erreur"] = None
                        st.rerun()  # rafraîchit la carte et le résumé

            if memoire.get("zone_erreur"):
                st.error(t["erreurs"][memoire["zone_erreur"]])


# Outils déjà fonctionnels : identifiant -> fonction qui les affiche.
# Les autres outils affichent encore un message "bientôt disponible".
OUTILS_ACTIFS = {
    "zone": _outil_importer_zone,
    "capteurs": outil_capteurs,
    "bandes": outil_bandes,
    "dates": outil_dates,
    "pretraitement": outil_pretraitement,
    "stacking": outil_stacking,
}


def _retirer_zone():
    memoire = st.session_state
    memoire["zone"] = None
    memoire["zone_erreur"] = None
    memoire["zone_fichier_id"] = None
    memoire["zone_uploader_n"] = memoire.get("zone_uploader_n", 0) + 1  # vide le champ d'envoi
    for cle in ("recherche", "pretraitement_etat", "pile"):
        memoire[cle] = None  # les résultats en aval ne correspondent plus à la zone


def _afficher_resume_zone(langue):
    """Affiche le résumé de la zone chargée (ou un message si aucune)."""
    t = TEXTES[langue]
    zone = st.session_state.get("zone")
    if zone is None:
        st.info(t["zone_aucune"])
        return

    st.success(t["zone_chargee"].format(nom=zone["nom"]))
    c1, c2, c3, c4 = st.columns([1, 1.3, 1.6, 1.4])
    c1.metric(t["zone_entites"], f"{zone['nb_entites']:,}".replace(",", " "))
    c2.metric(t["zone_superficie"], f"{zone['superficie_km2']:,.1f} km²".replace(",", " "))
    c3.metric(t["zone_crs"], zone["crs_origine"])
    c4.button(t["zone_retirer"], on_click=_retirer_zone, key="bouton_retirer_zone")
    if zone["crs_suppose"]:
        st.warning(t["zone_crs_suppose"])


# --------------------------------------------------------------------------
# Carte et flux
# --------------------------------------------------------------------------
def _couches_images():
    """Rassemble les couches d'images de toutes les étapes ; seule la dernière étape est visible."""
    memoire = st.session_state
    etapes = [
        (memoire.get("recherche") or {}).get("couches", []),
        (memoire.get("pretraitement_etat") or {}).get("couches", []),
        (memoire.get("pile") or {}).get("couches", []),
    ]
    derniere = max((i for i, couches in enumerate(etapes) if couches), default=-1)
    rassemblees = []
    for i, couches in enumerate(etapes):
        for couche in couches:
            rassemblees.append({**couche, "visible": couche["visible"] and i == derniere})
    return rassemblees


def _construire_carte(langue):
    """Construit la carte (fond satellite par défaut, fond plan en option)."""
    t = TEXTES[langue]
    # Vue de départ : centre de la RD Congo (utilisée tant qu'aucune zone n'est chargée).
    carte = folium.Map(location=[-2.5, 23.5], zoom_start=5, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr=t["attribution_esri"],
        name=t["satellite"],
        show=True,
    ).add_to(carte)
    folium.TileLayer("OpenStreetMap", name=t["plan"], show=False).add_to(carte)

    # Zone d'étude : contour jaune, sans remplissage opaque, et recentrage dessus.
    zone = st.session_state.get("zone")
    if zone is not None:
        folium.GeoJson(
            zone["gdf"].__geo_interface__,
            name=t["couche_zone"],
            style_function=lambda _: {"color": "#ffd400", "weight": 3, "fillColor": "#ffd400", "fillOpacity": 0.08},
        ).add_to(carte)
        ouest, sud, est, nord = zone["emprise"]
        carte.fit_bounds([[sud, ouest], [nord, est]])

    # Couches d'images (Earth Engine) : aperçus de la recherche (5b), des composites
    # prétraités et de la pile (5c). Seule l'étape la plus avancée est visible au départ.
    for couche in _couches_images():
        folium.TileLayer(
            tiles=couche["url"], attr="Google Earth Engine", name=couche["nom"],
            overlay=True, control=True, show=couche["visible"],
        ).add_to(carte)

    folium.LayerControl(collapsed=True).add_to(carte)
    return carte


def _afficher_flux(sous_etape, langue):
    """
    Affiche le flux procédural de la sous-étape :
    ✅ étape terminée, 🔵 étape en cours, ⚪ étape à venir.
    """
    etapes_flux = sous_etape["flux"][langue]

    # Nombre d'étapes terminées. Pour l'instant, seule la zone d'étude est suivie.
    # Aux étapes 5b à 7, on suivra l'avancement réel de chaque traitement.
    terminees = 0
    if sous_etape["id"] == "donnees" and st.session_state.get("zone") is not None:
        terminees = 1  # zone d'étude chargée
        if recherche_valide():
            terminees = 3  # images trouvées, bandes et indices choisis
            if pretraitement_valide():
                terminees = 4  # prétraitement appliqué
                if pile_valide():
                    terminees = 5  # stacking terminé

    morceaux = []
    for numero, nom in enumerate(etapes_flux):
        if numero < terminees:
            morceaux.append(f"✅ {nom}")
        elif numero == terminees:
            morceaux.append(f"**🔵 {nom}**")
        else:
            morceaux.append(f"⚪ {nom}")
    st.markdown("  →  ".join(morceaux))


# --------------------------------------------------------------------------
# Page complète
# --------------------------------------------------------------------------
def afficher_traitement(langue):
    """Affiche l'onglet Traitement : barre d'outils + écran divisé en deux."""
    t = TEXTES[langue]
    memoire = st.session_state
    memoire.setdefault("sous_etape", 0)  # index de la sous-étape active
    memoire.setdefault("zone", None)     # zone d'étude chargée (ou None)

    actuelle = SOUS_ETAPES[memoire.sous_etape]

    # ---- Titre de la sous-étape active ----
    st.subheader(f"{actuelle['icone']} {actuelle['nom'][langue]}")

    # ---- BARRE D'OUTILS (haut) : boutons de la sous-étape active ----
    st.caption(t["outils"])
    colonnes_outils = st.columns(len(actuelle["outils"]))
    for colonne, (id_outil, libelle_fr, libelle_en) in zip(colonnes_outils, actuelle["outils"]):
        libelle = libelle_fr if langue == "fr" else libelle_en
        with colonne:
            if id_outil in OUTILS_ACTIFS:
                OUTILS_ACTIFS[id_outil](langue)  # outil déjà construit
            elif st.button(libelle, key=f"outil_{actuelle['id']}_{id_outil}",
                           use_container_width=True):
                st.toast(t["bientot"].format(n=actuelle["etape_ou_dispo"]), icon="🛠️")

    # ---- Résumé de la zone et configuration des données (sous-étape Données) ----
    if actuelle["id"] == "donnees":
        auto_connexion()  # connexion automatique si un compte de service est configuré
        _afficher_resume_zone(langue)
        afficher_panneau_donnees(langue)
        afficher_panneau_pile(langue)

    st.divider()

    # ---- ÉCRAN DIVISÉ : gauche large / droite étroite ----
    gauche, droite = st.columns([14, 1.2])

    with droite:
        # Une icône par sous-étape. Le texte au survol vient de "help".
        for index, sous_etape in enumerate(SOUS_ETAPES):
            est_active = index == memoire.sous_etape
            if st.button(
                sous_etape["icone"],
                key=f"icone_{sous_etape['id']}",
                help=sous_etape["nom"][langue],
                type="primary" if est_active else "secondary",
                use_container_width=True,
            ):
                memoire.sous_etape = index
                st.rerun()

    with gauche:
        st.markdown(f"**{t['flux']}**")
        _afficher_flux(actuelle, langue)
        st.markdown(f"**{t['carte']}**")
        zone = memoire.get("zone")
        # La clé change avec la zone : la carte est reconstruite et recentrée.
        # La clé change dès que les couches changent : la carte est alors reconstruite.
        signature_couches = abs(hash(tuple(c["url"] + str(c["visible"]) for c in _couches_images())))
        cle_carte = f"carte_traitement_{zone['nom'] if zone else 'vide'}_{signature_couches}"
        st_folium(
            _construire_carte(langue),
            height=520,
            use_container_width=True,
            returned_objects=[],
            key=cle_carte,
        )
