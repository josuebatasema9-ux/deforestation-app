"""
outils_pretraitement_stacking.py
--------------------------------
Rôle : interface (Streamlit) des outils "Prétraitement" et "Stacking" de la
sous-étape "Données et prétraitement" :

  - outil_pretraitement()   : options de prétraitement par type d'image + bouton Appliquer
  - outil_stacking()        : choix de la résolution + lancement de l'assemblage
                              (disponible seulement une fois le prétraitement appliqué)
  - afficher_panneau_pile() : résumé de l'image finale et choix de la bande à afficher
  - pretraitement_valide(), pile_valide() : état d'avancement (pour le flux)

Le calcul est fait par pretraitement_stacking_earth_engine.py.
Les réglages sont conservés dans st.session_state["config"] (voir outils_donnees_satellitaires.py).
"""

import streamlit as st

from catalogue_capteurs_indices import CAPTEURS
from outils_donnees_satellitaires import (
    _capteurs_choisis,
    _enregistrer,
    _verifier_prerequis,
    configuration,
    recherche_valide,
    signature_configuration,
)
from pretraitement_stacking_earth_engine import (
    RESOLUTIONS_DISPONIBLES,
    bandes_rvb,
    decrire_bande,
    epsg_utm,
)

TEXTES = {
    "fr": {
        "lib_pretraitement": "🧹 Prétraitement",
        "lib_stacking": "🧱 Stacking",
        "lancer_recherche": "Lancez d'abord la recherche d'images (bouton « Rechercher les images »).",
        # --- optique ---
        "titre_optique": "Images optiques (Landsat, Sentinel-2)",
        "masque_nuages": "Masquer nuages, ombres et pixels défectueux",
        "aide_masque_nuages": "Landsat : bits de qualité QA_PIXEL. Sentinel-2 : classification SCL et probabilité de nuage.",
        "proba_nuage": "Probabilité de nuage maximale (Sentinel-2, %)",
        "masque_neige": "Masquer aussi la neige et la glace",
        "ecreter": "Corriger les valeurs aberrantes (réflectances ramenées entre 0 et 1)",
        "combler_vides": "Combler les petits vides (médiane du voisinage)",
        "rayon_comblement": "Rayon de comblement (m)",
        # --- radar ---
        "titre_radar": "Images radar (Sentinel-1)",
        "note_radar": "Calibration, bruit thermique et correction du relief sont déjà appliqués par Google.",
        "bruit_bord": "Masquer le bruit de bord (valeurs < −30 dB)",
        "aide_bruit_bord": "Approche simplifiée ; elle peut aussi retirer de l'eau très calme.",
        "filtre": "Filtre anti-speckle",
        "filtres": {"aucun": "Aucun", "mediane": "Médiane focale", "moyenne": "Moyenne focale (en linéaire)"},
        "rayon_filtre": "Rayon du filtre (m)",
        "composite_radar": "Composite temporel radar",
        "composites": {"mediane": "Médiane", "moyenne": "Moyenne (en linéaire)"},
        # --- application ---
        "bouton_appliquer": "Appliquer le prétraitement",
        "pretraitement_en_cours": "Préparation des composites prétraités…",
        "pretraitement_ok": "Prétraitement appliqué. Aperçus ajoutés à la carte (couches « prétraité »). Le bouton Stacking est maintenant disponible.",
        "pretraitement_perime": "La configuration a changé depuis le dernier prétraitement : appliquez-le de nouveau.",
        "erreur_pretraitement": "Le prétraitement a échoué : {detail}",
        # --- stacking ---
        "stacking_bloque": "Appliquez d'abord le prétraitement.",
        "titre_stacking": "Assemblage optique + radar + indices",
        "aide_stacking": "Assemble les bandes et indices choisis en une seule image multibande, découpée sur la zone d'étude.",
        "resolution": "Résolution finale (taille du pixel)",
        "note_grille": "Grille : UTM (EPSG:{epsg}), pixel de {m} m. Les bandes plus grossières sont rééchantillonnées au plus proche voisin.",
        "bouton_stacking": "Lancer le stacking",
        "stacking_en_cours": "Assemblage de l'image finale…",
        "erreur_stacking": "Le stacking a échoué : {detail}",
        # --- panneau pile ---
        "titre_pile": "Image finale (pile de bandes)",
        "nb_bandes": "Bandes",
        "resolution_pile": "Résolution",
        "systeme_pile": "Système de coordonnées",
        "pile_perimee": "La configuration a changé depuis le stacking : relancez-le.",
        "simplification": "Le contour de la zone a été simplifié d'environ {m} m pour le découpage.",
        "avertissement_bandes": "Les bandes obtenues diffèrent de celles prévues. Vérifiez la liste ci-dessous.",
        "afficher": "Afficher sur la carte",
        "rvb": "Couleurs naturelles (RVB)",
        "liste_bandes": "Liste des bandes",
        "col_bande": "Bande",
        "col_origine": "Origine",
        "origines": {"bande": "bande", "indice": "indice"},
        "note_calcul": "L'image est calculée à la demande par Google : l'affichage de la carte peut prendre quelques secondes.",
    },
    "en": {
        "lib_pretraitement": "🧹 Preprocessing",
        "lib_stacking": "🧱 Stacking",
        "lancer_recherche": "Run the image search first (“Search images” button).",
        "titre_optique": "Optical images (Landsat, Sentinel-2)",
        "masque_nuages": "Mask clouds, shadows and defective pixels",
        "aide_masque_nuages": "Landsat: QA_PIXEL quality bits. Sentinel-2: SCL classification and cloud probability.",
        "proba_nuage": "Maximum cloud probability (Sentinel-2, %)",
        "masque_neige": "Also mask snow and ice",
        "ecreter": "Fix outliers (reflectance clipped to 0–1)",
        "combler_vides": "Fill small gaps (neighborhood median)",
        "rayon_comblement": "Gap-filling radius (m)",
        "titre_radar": "Radar images (Sentinel-1)",
        "note_radar": "Calibration, thermal noise removal and terrain correction are already applied by Google.",
        "bruit_bord": "Mask border noise (values < −30 dB)",
        "aide_bruit_bord": "Simplified approach; it may also remove very calm water.",
        "filtre": "Speckle filter",
        "filtres": {"aucun": "None", "mediane": "Focal median", "moyenne": "Focal mean (in linear)"},
        "rayon_filtre": "Filter radius (m)",
        "composite_radar": "Radar temporal composite",
        "composites": {"mediane": "Median", "moyenne": "Mean (in linear)"},
        "bouton_appliquer": "Apply preprocessing",
        "pretraitement_en_cours": "Preparing preprocessed composites…",
        "pretraitement_ok": "Preprocessing applied. Previews added to the map (“preprocessed” layers). The Stacking button is now available.",
        "pretraitement_perime": "The configuration changed since the last preprocessing: apply it again.",
        "erreur_pretraitement": "Preprocessing failed: {detail}",
        "stacking_bloque": "Apply the preprocessing first.",
        "titre_stacking": "Optical + radar + indices assembly",
        "aide_stacking": "Assembles the chosen bands and indices into a single multiband image, clipped to the study area.",
        "resolution": "Final resolution (pixel size)",
        "note_grille": "Grid: UTM (EPSG:{epsg}), {m} m pixel. Coarser bands are resampled with nearest neighbor.",
        "bouton_stacking": "Run stacking",
        "stacking_en_cours": "Assembling the final image…",
        "erreur_stacking": "Stacking failed: {detail}",
        "titre_pile": "Final image (band stack)",
        "nb_bandes": "Bands",
        "resolution_pile": "Resolution",
        "systeme_pile": "Coordinate system",
        "pile_perimee": "The configuration changed since the stacking: run it again.",
        "simplification": "The study area outline was simplified by about {m} m for clipping.",
        "avertissement_bandes": "The bands obtained differ from those planned. Check the list below.",
        "afficher": "Show on the map",
        "rvb": "Natural colors (RGB)",
        "liste_bandes": "Band list",
        "col_bande": "Band",
        "col_origine": "Origin",
        "origines": {"bande": "band", "indice": "index"},
        "note_calcul": "The image is computed on demand by Google: the map may take a few seconds to display.",
    },
}


# --------------------------------------------------------------------------
# État d'avancement
# --------------------------------------------------------------------------
def pretraitement_valide():
    """True si un prétraitement a été appliqué avec la configuration actuelle."""
    etat = st.session_state.get("pretraitement_etat")
    if not etat or not recherche_valide():
        return False
    zone = st.session_state.get("zone")
    return etat["signature"] == signature_configuration(zone, ignorer=("resolution_m",))


def pile_valide():
    """True si le stacking correspond à la configuration actuelle."""
    pile = st.session_state.get("pile")
    if not pile:
        return False
    return pile["signature"] == signature_configuration(st.session_state.get("zone"), ignorer=())


# --------------------------------------------------------------------------
# Outil : Prétraitement
# --------------------------------------------------------------------------
def outil_pretraitement(langue):
    t = TEXTES[langue]
    memoire = st.session_state
    cfg = configuration()
    pre = cfg["pretraitement"]
    choisis = _capteurs_choisis()

    with st.popover(t["lib_pretraitement"], use_container_width=True):
        if not recherche_valide():
            st.info(t["lancer_recherche"])
            return

        # ---- Optique ----
        if any(CAPTEURS[c]["type"] == "optique" for c in choisis):
            st.markdown(f"**{t['titre_optique']}**")
            st.checkbox(t["masque_nuages"], value=pre["optique"]["masque_nuages"],
                        help=t["aide_masque_nuages"], key="w_pre_masque",
                        on_change=_enregistrer,
                        args=("w_pre_masque", "pretraitement", "optique", "masque_nuages"))
            if pre["optique"]["masque_nuages"]:
                if "sentinel2" in choisis:
                    st.slider(t["proba_nuage"], 0, 100, value=pre["optique"]["proba_nuage_s2"],
                              step=5, key="w_pre_proba", on_change=_enregistrer,
                              args=("w_pre_proba", "pretraitement", "optique", "proba_nuage_s2"))
                st.checkbox(t["masque_neige"], value=pre["optique"]["masque_neige"],
                            key="w_pre_neige", on_change=_enregistrer,
                            args=("w_pre_neige", "pretraitement", "optique", "masque_neige"))
            st.checkbox(t["ecreter"], value=pre["optique"]["ecreter"], key="w_pre_ecreter",
                        on_change=_enregistrer,
                        args=("w_pre_ecreter", "pretraitement", "optique", "ecreter"))
            st.checkbox(t["combler_vides"], value=pre["optique"]["combler_vides"],
                        key="w_pre_combler", on_change=_enregistrer,
                        args=("w_pre_combler", "pretraitement", "optique", "combler_vides"))
            if pre["optique"]["combler_vides"]:
                st.slider(t["rayon_comblement"], 30, 150, value=pre["optique"]["rayon_comblement_m"],
                          step=30, key="w_pre_rayon_c", on_change=_enregistrer,
                          args=("w_pre_rayon_c", "pretraitement", "optique", "rayon_comblement_m"))

        # ---- Radar ----
        if "sentinel1" in choisis:
            st.markdown(f"**{t['titre_radar']}**")
            st.caption(t["note_radar"])
            st.checkbox(t["bruit_bord"], value=pre["radar"]["bruit_bord"],
                        help=t["aide_bruit_bord"], key="w_pre_bord", on_change=_enregistrer,
                        args=("w_pre_bord", "pretraitement", "radar", "bruit_bord"))
            options_filtre = list(t["filtres"].keys())
            st.selectbox(t["filtre"], options_filtre,
                         index=options_filtre.index(pre["radar"]["filtre"]),
                         format_func=lambda x: t["filtres"][x], key="w_pre_filtre",
                         on_change=_enregistrer,
                         args=("w_pre_filtre", "pretraitement", "radar", "filtre"))
            if pre["radar"]["filtre"] != "aucun":
                st.slider(t["rayon_filtre"], 10, 100, value=pre["radar"]["rayon_filtre_m"],
                          step=10, key="w_pre_rayon_f", on_change=_enregistrer,
                          args=("w_pre_rayon_f", "pretraitement", "radar", "rayon_filtre_m"))
            options_composite = list(t["composites"].keys())
            st.radio(t["composite_radar"], options_composite,
                     index=options_composite.index(pre["radar"]["composite"]),
                     format_func=lambda x: t["composites"][x], horizontal=True,
                     key="w_pre_composite", on_change=_enregistrer,
                     args=("w_pre_composite", "pretraitement", "radar", "composite"))

        st.divider()
        if st.button(t["bouton_appliquer"], type="primary", key="bouton_pretraitement"):
            probleme = _verifier_prerequis(langue)
            if probleme:
                st.warning(probleme)
            else:
                from pretraitement_stacking_earth_engine import apercus_pretraites
                try:
                    with st.spinner(t["pretraitement_en_cours"]):
                        apercus = apercus_pretraites(memoire["zone"]["gdf"], cfg)
                except Exception as erreur:
                    st.error(t["erreur_pretraitement"].format(detail=str(erreur)[:300]))
                else:
                    memoire["pretraitement_etat"] = {
                        "signature": signature_configuration(memoire["zone"], ignorer=("resolution_m",)),
                        "couches": apercus["couches"],
                    }
                    memoire["pile"] = None  # l'ancienne pile n'est plus à jour
                    st.rerun()

        etat = memoire.get("pretraitement_etat")
        if etat:
            if pretraitement_valide():
                st.success(t["pretraitement_ok"])
            else:
                st.warning(t["pretraitement_perime"])


# --------------------------------------------------------------------------
# Outil : Stacking
# --------------------------------------------------------------------------
def outil_stacking(langue):
    t = TEXTES[langue]
    memoire = st.session_state
    cfg = configuration()
    disponible = pretraitement_valide()

    with st.popover(t["lib_stacking"], use_container_width=True, disabled=not disponible,
                    help=None if disponible else t["stacking_bloque"]):
        st.markdown(f"**{t['titre_stacking']}**")
        st.caption(t["aide_stacking"])
        st.radio(t["resolution"], list(RESOLUTIONS_DISPONIBLES),
                 index=list(RESOLUTIONS_DISPONIBLES).index(cfg["resolution_m"]),
                 format_func=lambda m: f"{m} m", horizontal=True, key="w_resolution",
                 on_change=_enregistrer, args=("w_resolution", "resolution_m"))
        zone = memoire.get("zone")
        if zone:
            st.caption(t["note_grille"].format(epsg=epsg_utm(zone["emprise"]), m=cfg["resolution_m"]))

        if st.button(t["bouton_stacking"], type="primary", key="bouton_stacking"):
            from pretraitement_stacking_earth_engine import construire_pile, couche_pile
            try:
                with st.spinner(t["stacking_en_cours"]):
                    pile = construire_pile(zone["gdf"], cfg, cfg["resolution_m"])
                    choix = "rvb" if bandes_rvb(pile["bandes"]) else pile["bandes"][0]
                    pile["choix"] = choix
                    pile["couches"] = [couche_pile(pile, choix)]
                    pile["cache_urls"] = {choix: pile["couches"][0]["url"]}
            except Exception as erreur:
                st.error(t["erreur_stacking"].format(detail=str(erreur)[:300]))
            else:
                pile["signature"] = signature_configuration(zone, ignorer=())
                pile["numero"] = (memoire.get("pile") or {}).get("numero", 0) + 1
                memoire["pile"] = pile
                st.rerun()


# --------------------------------------------------------------------------
# Panneau : résumé de la pile + choix de la bande à afficher
# --------------------------------------------------------------------------
def afficher_panneau_pile(langue):
    t = TEXTES[langue]
    memoire = st.session_state
    pile = memoire.get("pile")
    if not pile:
        return

    with st.container(border=True):
        st.markdown(f"**{t['titre_pile']}**")
        c1, c2, c3 = st.columns(3)
        c1.metric(t["nb_bandes"], len(pile["bandes"]))
        c2.metric(t["resolution_pile"], f"{pile['echelle']} m")
        c3.metric(t["systeme_pile"], pile["crs"])

        if not pile_valide():
            st.warning(t["pile_perimee"])
        if pile["avertissement"]:
            st.warning(t["avertissement_bandes"])
        if pile["tolerance_m"] > 0:
            st.caption(t["simplification"].format(m=pile["tolerance_m"]))

        # ---- Choix de l'affichage ----
        options = (["rvb"] if bandes_rvb(pile["bandes"]) else []) + list(pile["bandes"])
        choix = st.selectbox(
            t["afficher"], options, index=options.index(pile["choix"]),
            format_func=lambda x: t["rvb"] if x == "rvb" else x, key="w_bande_pile",
        )
        if choix != pile["choix"]:
            from pretraitement_stacking_earth_engine import couche_pile
            if choix not in pile["cache_urls"]:
                pile["cache_urls"][choix] = couche_pile(pile, choix)["url"]
            nom = "Pile – RVB" if choix == "rvb" else f"Pile – {choix}"
            pile["couches"] = [{"nom": nom, "url": pile["cache_urls"][choix], "visible": True}]
            pile["choix"] = choix
            pile["numero"] += 1  # force la reconstruction de la carte
        st.caption(t["note_calcul"])

        with st.expander(t["liste_bandes"]):
            lignes = [decrire_bande(nom, langue) for nom in pile["bandes"]]
            st.table({
                t["col_bande"]: list(pile["bandes"]),
                t["col_origine"]: [f"{capteur} · {t['origines'][genre]}" for capteur, genre in lignes],
            })
