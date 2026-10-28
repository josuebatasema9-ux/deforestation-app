"""
outils_donnees_satellitaires.py
-------------------------------
Rôle : interface (Streamlit) des outils de la sous-étape "Données et prétraitement"
qui concernent les images satellitaires :

  - outil_capteurs()  : connexion à Earth Engine + choix des capteurs, nuages, orbite
  - outil_bandes()    : choix des bandes et des indices spectraux
  - outil_dates()     : période d'étude
  - afficher_panneau_donnees() : résumé de la configuration + recherche des images

Le choix de l'utilisateur est gardé dans st.session_state["config"], pour ne pas
être perdu quand on change de sous-étape.
La recherche d'images elle-même est dans recherche_images_earth_engine.py.
"""

import os
from datetime import date, timedelta

import streamlit as st

from catalogue_capteurs_indices import (
    BANDES_OPTIQUES_LIBELLES,
    CAPTEURS,
    INDICES_OPTIQUES,
    INDICES_SAR,
)
from connexion_earth_engine import initialiser_earth_engine, lire_compte_service

TEXTES = {
    "fr": {
        "lib_capteurs": "🛰️ Capteurs et API",
        "lib_bandes": "🎚️ Bandes et indices",
        "lib_dates": "📅 Dates",
        # --- connexion ---
        "titre_connexion": "Connexion à Google Earth Engine",
        "aide_connexion": "Earth Engine fournit Landsat 8/9, Sentinel-1 et Sentinel-2.",
        "projet": "Identifiant du projet Google Cloud",
        "projet_aide": "Exemple : mon-projet-123456 (projet enregistré pour Earth Engine).",
        "bouton_connexion": "Se connecter à Earth Engine",
        "connexion_en_cours": "Connexion à Earth Engine…",
        "ok_compte_service": "Connecté (compte de service, projet : {detail}).",
        "ok_local": "Connecté (compte personnel, projet : {detail}).",
        "non_connecte": "Non connecté à Earth Engine.",
        "ee_absent": "La bibliothèque earthengine-api n'est pas installée. Lancez : pip install -r requirements.txt",
        "projet_requis": "Saisissez l'identifiant de votre projet Google Cloud.",
        "non_authentifie": (
            "Authentification requise. Dans le terminal (avec venv actif), lancez une fois : "
            "python -c \"import ee; ee.Authenticate()\" puis réessayez."
        ),
        "erreur": "Échec de la connexion : {detail}",
        # --- capteurs ---
        "titre_capteurs": "Capteurs à utiliser",
        "nuages": "Nuages maximum par image (optique, %)",
        "orbite": "Orbite Sentinel-1",
        "orbite_options": {"BOTH": "Toutes", "ASCENDING": "Ascendante", "DESCENDING": "Descendante"},
        # --- bandes ---
        "titre_bandes": "Bandes",
        "bandes_de": "Bandes {capteur}",
        "titre_indices": "Indices spectraux",
        "indices_optiques": "Indices optiques",
        "indices_sar": "Indices radar",
        "aucun_capteur": "Choisissez d'abord au moins un capteur (outil « Capteurs et API »).",
        "note_indices": "Les bandes nécessaires aux indices sont chargées automatiquement.",
        "choisir": "Choisir des options",
        # --- dates ---
        "date_debut": "Date de début",
        "date_fin": "Date de fin",
        "date_invalide": "La date de début doit précéder la date de fin.",
        "avant_dispo": "{capteur} n'existe pas avant le {date}.",
        # --- panneau ---
        "titre_panneau": "Configuration des données",
        "ligne_capteurs": "**Capteurs** : {valeur}",
        "ligne_periode": "**Période** : du {debut} au {fin}",
        "ligne_bandes": "**Bandes** — {capteur} : {valeur}",
        "ligne_indices": "**Indices** : {valeur}",
        "ligne_nuages": "**Nuages max.** : {valeur} %",
        "aucun": "aucun",
        "bouton_recherche": "🔎 Rechercher les images",
        "recherche_en_cours": "Interrogation d'Earth Engine…",
        "manque_zone": "Importez d'abord la zone d'étude.",
        "manque_connexion": "Connectez-vous d'abord à Earth Engine (outil « Capteurs et API »).",
        "manque_capteur": "Choisissez au moins un capteur.",
        "manque_bandes": "Choisissez au moins une bande pour {capteur}.",
        "resultats": "Images trouvées",
        "col_capteur": "Capteur",
        "col_nombre": "Nombre d'images",
        "aucune_image": "Aucune image trouvée pour {capteur} : élargissez la période ou la tolérance aux nuages.",
        "apercu_info": "Les aperçus (composite médian, sans masque de nuages) sont sur la carte : ouvrez le sélecteur de couches en haut à droite.",
        "resultats_perimes": "La configuration a changé depuis la dernière recherche : relancez la recherche.",
        "erreur_recherche": "La recherche a échoué : {detail}",
    },
    "en": {
        "lib_capteurs": "🛰️ Sensors and API",
        "lib_bandes": "🎚️ Bands and indices",
        "lib_dates": "📅 Dates",
        "titre_connexion": "Google Earth Engine connection",
        "aide_connexion": "Earth Engine provides Landsat 8/9, Sentinel-1 and Sentinel-2.",
        "projet": "Google Cloud project ID",
        "projet_aide": "Example: my-project-123456 (project registered for Earth Engine).",
        "bouton_connexion": "Connect to Earth Engine",
        "connexion_en_cours": "Connecting to Earth Engine…",
        "ok_compte_service": "Connected (service account, project: {detail}).",
        "ok_local": "Connected (personal account, project: {detail}).",
        "non_connecte": "Not connected to Earth Engine.",
        "ee_absent": "The earthengine-api library is not installed. Run: pip install -r requirements.txt",
        "projet_requis": "Enter your Google Cloud project ID.",
        "non_authentifie": (
            "Authentication required. In the terminal (venv active), run once: "
            "python -c \"import ee; ee.Authenticate()\" then try again."
        ),
        "erreur": "Connection failed: {detail}",
        "titre_capteurs": "Sensors to use",
        "nuages": "Maximum cloud cover per image (optical, %)",
        "orbite": "Sentinel-1 orbit",
        "orbite_options": {"BOTH": "All", "ASCENDING": "Ascending", "DESCENDING": "Descending"},
        "titre_bandes": "Bands",
        "bandes_de": "{capteur} bands",
        "titre_indices": "Spectral indices",
        "indices_optiques": "Optical indices",
        "indices_sar": "Radar indices",
        "aucun_capteur": "Choose at least one sensor first (“Sensors and API” tool).",
        "note_indices": "Bands needed by the indices are loaded automatically.",
        "choisir": "Choose options",
        "date_debut": "Start date",
        "date_fin": "End date",
        "date_invalide": "The start date must be before the end date.",
        "avant_dispo": "{capteur} does not exist before {date}.",
        "titre_panneau": "Data configuration",
        "ligne_capteurs": "**Sensors**: {valeur}",
        "ligne_periode": "**Period**: from {debut} to {fin}",
        "ligne_bandes": "**Bands** — {capteur}: {valeur}",
        "ligne_indices": "**Indices**: {valeur}",
        "ligne_nuages": "**Max. clouds**: {valeur} %",
        "aucun": "none",
        "bouton_recherche": "🔎 Search images",
        "recherche_en_cours": "Querying Earth Engine…",
        "manque_zone": "Import the study area first.",
        "manque_connexion": "Connect to Earth Engine first (“Sensors and API” tool).",
        "manque_capteur": "Choose at least one sensor.",
        "manque_bandes": "Choose at least one band for {capteur}.",
        "resultats": "Images found",
        "col_capteur": "Sensor",
        "col_nombre": "Number of images",
        "aucune_image": "No image found for {capteur}: widen the period or the cloud tolerance.",
        "apercu_info": "Previews (median composite, no cloud mask) are on the map: open the layer selector at the top right.",
        "resultats_perimes": "The configuration changed since the last search: search again.",
        "erreur_recherche": "The search failed: {detail}",
    },
}


# --------------------------------------------------------------------------
# Configuration conservée en mémoire (survit au changement de sous-étape)
# --------------------------------------------------------------------------
def configuration():
    """Retourne la configuration de l'utilisateur (créée avec des valeurs par défaut)."""
    memoire = st.session_state
    if "config" not in memoire:
        aujourdhui = date.today()
        memoire["config"] = {
            "capteurs": {"landsat": False, "sentinel2": True, "sentinel1": True},
            "nuages_max": 30,
            "orbite": "BOTH",
            "bandes": {
                "landsat": ["blue", "green", "red", "nir", "swir1", "swir2"],
                "sentinel2": ["blue", "green", "red", "nir", "swir1", "swir2"],
                "sentinel1": ["VV", "VH"],
            },
            "indices_optiques": ["NDVI"],
            "indices_sar": [],
            "date_debut": aujourdhui - timedelta(days=180),
            "date_fin": aujourdhui,
        }
    # Réglages ajoutés à l'étape 5c (aussi ajoutés si la session date d'une version précédente)
    memoire["config"].setdefault("pretraitement", {
        "optique": {
            "masque_nuages": True,        # nuages, ombres, cirrus, pixels défectueux
            "proba_nuage_s2": 40,         # Sentinel-2 : probabilité de nuage maximale (%)
            "masque_neige": False,
            "ecreter": True,              # réflectances ramenées entre 0 et 1
            "combler_vides": True,
            "rayon_comblement_m": 60,
        },
        "radar": {
            "bruit_bord": True,
            "filtre": "mediane",          # "aucun", "mediane" ou "moyenne"
            "rayon_filtre_m": 30,
            "composite": "mediane",       # "mediane" ou "moyenne"
        },
    })
    memoire["config"].setdefault("resolution_m", 30)  # résolution finale de la pile
    return memoire["config"]


def _enregistrer(cle_widget, *chemin):
    """Copie la valeur d'un widget dans la configuration (appelé à chaque changement)."""
    cible = configuration()
    for etape in chemin[:-1]:
        cible = cible[etape]
    cible[chemin[-1]] = st.session_state[cle_widget]


def _capteurs_choisis():
    cfg = configuration()
    return [cle for cle, actif in cfg["capteurs"].items() if actif]


# --------------------------------------------------------------------------
# Connexion automatique (compte de service en ligne)
# --------------------------------------------------------------------------
def auto_connexion():
    """Si un compte de service est configuré, se connecte une seule fois, sans clic."""
    memoire = st.session_state
    if "ee_etat" not in memoire and lire_compte_service():
        ok, code, detail = initialiser_earth_engine()
        memoire["ee_etat"] = {"ok": ok, "code": code, "detail": detail}


def earth_engine_connecte():
    etat = st.session_state.get("ee_etat")
    return bool(etat and etat["ok"])


# --------------------------------------------------------------------------
# Outil : Capteurs et API
# --------------------------------------------------------------------------
def outil_capteurs(langue):
    t = TEXTES[langue]
    memoire = st.session_state
    cfg = configuration()

    with st.popover(t["lib_capteurs"], use_container_width=True):
        # ---- Connexion ----
        st.markdown(f"**{t['titre_connexion']}**")
        st.caption(t["aide_connexion"])
        projet = st.text_input(
            t["projet"],
            value=memoire.get("ee_projet", os.environ.get("EE_PROJECT", "")),
            help=t["projet_aide"],
            key="w_ee_projet",
            disabled=lire_compte_service() is not None,
        )
        if st.button(t["bouton_connexion"], key="bouton_ee"):
            memoire["ee_projet"] = projet
            with st.spinner(t["connexion_en_cours"]):
                ok, code, detail = initialiser_earth_engine(projet)
            memoire["ee_etat"] = {"ok": ok, "code": code, "detail": detail}

        etat = memoire.get("ee_etat")
        if etat is None:
            st.info(t["non_connecte"])
        elif etat["ok"]:
            st.success(t[etat["code"]].format(detail=etat["detail"]))
        else:
            st.error(t[etat["code"]].format(detail=etat["detail"]))

        st.divider()

        # ---- Capteurs ----
        st.markdown(f"**{t['titre_capteurs']}**")
        for cle, capteur in CAPTEURS.items():
            st.checkbox(
                capteur["nom"][langue],
                value=cfg["capteurs"][cle],
                key=f"w_capteur_{cle}",
                on_change=_enregistrer,
                args=(f"w_capteur_{cle}", "capteurs", cle),
            )
        st.slider(
            t["nuages"], 0, 100, value=cfg["nuages_max"], step=5,
            key="w_nuages", on_change=_enregistrer, args=("w_nuages", "nuages_max"),
        )
        st.radio(
            t["orbite"], list(t["orbite_options"].keys()),
            index=list(t["orbite_options"].keys()).index(cfg["orbite"]),
            format_func=lambda x: t["orbite_options"][x], horizontal=True,
            key="w_orbite", on_change=_enregistrer, args=("w_orbite", "orbite"),
        )


# --------------------------------------------------------------------------
# Outil : Bandes et indices
# --------------------------------------------------------------------------
def outil_bandes(langue):
    t = TEXTES[langue]
    cfg = configuration()
    choisis = _capteurs_choisis()

    with st.popover(t["lib_bandes"], use_container_width=True):
        if not choisis:
            st.info(t["aucun_capteur"])
            return

        st.markdown(f"**{t['titre_bandes']}**")
        for cle in choisis:
            capteur = CAPTEURS[cle]
            if capteur["type"] == "optique":
                options = list(capteur["bandes"].keys())
                libelle = lambda b: BANDES_OPTIQUES_LIBELLES[b][langue]
            else:
                options = list(capteur["bandes"])
                libelle = lambda b: b
            st.multiselect(
                t["bandes_de"].format(capteur=capteur["nom_court"][langue]),
                options, default=[b for b in cfg["bandes"][cle] if b in options],
                format_func=libelle, placeholder=t["choisir"],
                key=f"w_bandes_{cle}", on_change=_enregistrer,
                args=(f"w_bandes_{cle}", "bandes", cle),
            )

        st.markdown(f"**{t['titre_indices']}**")
        if any(CAPTEURS[c]["type"] == "optique" for c in choisis):
            st.multiselect(
                t["indices_optiques"], list(INDICES_OPTIQUES.keys()),
                default=cfg["indices_optiques"], placeholder=t["choisir"],
                format_func=lambda i: f"{i} — {INDICES_OPTIQUES[i][langue]}",
                key="w_indices_optiques", on_change=_enregistrer,
                args=("w_indices_optiques", "indices_optiques"),
            )
            st.caption(t["note_indices"])
        if "sentinel1" in choisis:
            st.multiselect(
                t["indices_sar"], list(INDICES_SAR.keys()),
                default=cfg["indices_sar"], placeholder=t["choisir"],
                format_func=lambda i: f"{i} — {INDICES_SAR[i][langue]}",
                key="w_indices_sar", on_change=_enregistrer,
                args=("w_indices_sar", "indices_sar"),
            )


# --------------------------------------------------------------------------
# Outil : Dates
# --------------------------------------------------------------------------
def outil_dates(langue):
    t = TEXTES[langue]
    cfg = configuration()

    with st.popover(t["lib_dates"], use_container_width=True):
        st.date_input(
            t["date_debut"], value=cfg["date_debut"], min_value=date(2013, 1, 1),
            max_value=date.today(), key="w_date_debut",
            on_change=_enregistrer, args=("w_date_debut", "date_debut"),
        )
        st.date_input(
            t["date_fin"], value=cfg["date_fin"], min_value=date(2013, 1, 1),
            max_value=date.today(), key="w_date_fin",
            on_change=_enregistrer, args=("w_date_fin", "date_fin"),
        )
        if cfg["date_debut"] > cfg["date_fin"]:
            st.error(t["date_invalide"])
        for cle in _capteurs_choisis():
            date_min = date.fromisoformat(CAPTEURS[cle]["date_min"])
            if cfg["date_debut"] < date_min:
                st.warning(t["avant_dispo"].format(
                    capteur=CAPTEURS[cle]["nom_court"][langue], date=date_min.isoformat()))


# --------------------------------------------------------------------------
# Panneau : résumé de la configuration + recherche d'images
# --------------------------------------------------------------------------
def signature_configuration(zone, ignorer=("pretraitement", "resolution_m")):
    """
    Empreinte de la configuration et de la zone, pour détecter un résultat périmé.
    On peut ignorer certains réglages : la recherche d'images, par exemple, ne dépend
    pas des options de prétraitement ni de la résolution finale.
    """
    cfg = {cle: valeur for cle, valeur in configuration().items() if cle not in ignorer}
    return repr((cfg, zone["nom"] if zone else None))


def _signature(zone):
    return signature_configuration(zone)


def _verifier_prerequis(langue):
    """Retourne un message d'erreur (texte) si la recherche est impossible, sinon None."""
    t = TEXTES[langue]
    cfg = configuration()
    choisis = _capteurs_choisis()
    if st.session_state.get("zone") is None:
        return t["manque_zone"]
    if not earth_engine_connecte():
        return t["manque_connexion"]
    if not choisis:
        return t["manque_capteur"]
    if cfg["date_debut"] > cfg["date_fin"]:
        return t["date_invalide"]
    for cle in choisis:
        if not cfg["bandes"][cle]:
            return t["manque_bandes"].format(capteur=CAPTEURS[cle]["nom_court"][langue])
    return None


def afficher_panneau_donnees(langue):
    """Résumé de la configuration, bouton de recherche et résultats."""
    t = TEXTES[langue]
    memoire = st.session_state
    cfg = configuration()
    choisis = _capteurs_choisis()
    zone = memoire.get("zone")

    with st.container(border=True):
        st.markdown(f"**{t['titre_panneau']}**")
        noms = ", ".join(CAPTEURS[c]["nom_court"][langue] for c in choisis) or t["aucun"]
        st.markdown(t["ligne_capteurs"].format(valeur=noms))
        st.markdown(t["ligne_periode"].format(
            debut=cfg["date_debut"].isoformat(), fin=cfg["date_fin"].isoformat()))
        for cle in choisis:
            if CAPTEURS[cle]["type"] == "optique":
                bandes = ", ".join(BANDES_OPTIQUES_LIBELLES[b][langue] for b in cfg["bandes"][cle])
            else:
                bandes = ", ".join(cfg["bandes"][cle])
            st.markdown(t["ligne_bandes"].format(
                capteur=CAPTEURS[cle]["nom_court"][langue], valeur=bandes or t["aucun"]))
        indices = list(cfg["indices_optiques"]) + list(cfg["indices_sar"])
        st.markdown(t["ligne_indices"].format(valeur=", ".join(indices) or t["aucun"]))
        if any(CAPTEURS[c]["type"] == "optique" for c in choisis):
            st.markdown(t["ligne_nuages"].format(valeur=cfg["nuages_max"]))

        if st.button(t["bouton_recherche"], type="primary", key="bouton_recherche"):
            probleme = _verifier_prerequis(langue)
            if probleme:
                st.warning(probleme)
            else:
                # Import tardif : ce module charge la bibliothèque ee
                from recherche_images_earth_engine import rechercher_images
                try:
                    with st.spinner(t["recherche_en_cours"]):
                        resultat = rechercher_images(zone["gdf"], cfg)
                except Exception as erreur:
                    st.error(t["erreur_recherche"].format(detail=str(erreur)[:300]))
                else:
                    resultat["signature"] = _signature(zone)
                    resultat["numero"] = memoire.get("recherche", {}).get("numero", 0) + 1
                    memoire["recherche"] = resultat
                    st.rerun()  # la carte doit être reconstruite avec les aperçus

        # ---- Résultats de la dernière recherche ----
        recherche = memoire.get("recherche")
        if recherche:
            if recherche["signature"] != _signature(zone):
                st.warning(t["resultats_perimes"])
            st.markdown(f"**{t['resultats']}**")
            lignes = {
                t["col_capteur"]: [CAPTEURS[c]["nom_court"][langue] for c in recherche["nb"]],
                t["col_nombre"]: list(recherche["nb"].values()),
            }
            st.table(lignes)
            for cle, nombre in recherche["nb"].items():
                if nombre == 0:
                    st.warning(t["aucune_image"].format(capteur=CAPTEURS[cle]["nom_court"][langue]))
            if recherche["couches"]:
                st.info(t["apercu_info"])


def recherche_valide():
    """True si une recherche réussie correspond à la configuration actuelle."""
    recherche = st.session_state.get("recherche")
    if not recherche or not recherche["couches"]:
        return False
    return recherche["signature"] == _signature(st.session_state.get("zone"))
