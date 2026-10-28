"""
pretraitement_stacking_earth_engine.py
--------------------------------------
Rôle : à partir de la configuration de l'utilisateur,
  1. fabriquer, pour chaque capteur, une image COMPOSITE PRÉTRAITÉE
     (nuages masqués, vides comblés, speckle filtré...) ;
  2. assembler ces composites, leurs bandes et leurs indices en UNE SEULE image
     multibande : la "pile" (stacking), découpée sur la zone d'étude.

Rien n'est téléchargé ici : Earth Engine garde la pile sous forme de recette de
calcul, exécutée par les serveurs de Google quand on affiche ou exporte l'image.
La pile sera utilisée telle quelle aux étapes 6 et 7 (extraction des valeurs aux
points d'entraînement, classification).

Noms des bandes de la pile : PRÉFIXE_bande, avec L = Landsat 8/9, S2 = Sentinel-2,
S1 = Sentinel-1. Exemples : S2_red, S2_NDVI, S1_VV, S1_VH_VV, L_nir.

Ce fichier ne contient AUCUN affichage Streamlit.
"""

import ee

from catalogue_capteurs_indices import (
    APERCU_OPTIQUE,
    APERCU_SAR_VV,
    CAPTEURS,
    INDICES_OPTIQUES,
    INDICES_SAR,
)
from filtres_masques_earth_engine import (
    combler_vides,
    composite_radar,
    ecreter_reflectance,
    filtre_speckle,
)
from recherche_images_earth_engine import (
    PALETTE_INDICE,
    calculer_indice_optique,
    collection_optique,
    collection_radar,
    geometrie_et_tolerance,
)

PREFIXES = {"landsat": "L", "sentinel2": "S2", "sentinel1": "S1"}
ORDRE_CAPTEURS = ("landsat", "sentinel2", "sentinel1")

# Pour le découpage final, la zone est simplifiée beaucoup moins que pour la recherche
MAX_COORDONNEES_DECOUPAGE = 30000
TOLERANCES_DECOUPAGE = (0, 0.0001, 0.0003, 0.001)  # degrés (0,0001° ≈ 10 m)

RESOLUTIONS_DISPONIBLES = (10, 20, 30)


# --------------------------------------------------------------------------
# Fonctions Python simples (sans Earth Engine) : noms, grille, visualisation
# --------------------------------------------------------------------------
def capteurs_actifs(configuration):
    return [c for c in ORDRE_CAPTEURS if configuration["capteurs"].get(c)]


def polarisations_necessaires(configuration):
    """Polarisations radar à charger : celles choisies + VV et VH si un indice radar est demandé."""
    pol = set(configuration["bandes"]["sentinel1"])
    if configuration["indices_sar"]:
        pol |= {"VV", "VH"}
    return sorted(pol)


def noms_bandes_pile(configuration):
    """Liste ordonnée des noms de bandes de la pile (calculée sans appeler Earth Engine)."""
    noms = []
    for cle in capteurs_actifs(configuration):
        prefixe = PREFIXES[cle]
        if CAPTEURS[cle]["type"] == "optique":
            noms += [f"{prefixe}_{b}" for b in configuration["bandes"][cle]]
            noms += [f"{prefixe}_{i}" for i in configuration["indices_optiques"]]
        else:
            noms += [f"{prefixe}_{b}" for b in configuration["bandes"][cle]]
            noms += [f"{prefixe}_{i}" for i in configuration["indices_sar"]]
    return noms


def epsg_utm(emprise):
    """Code EPSG de la zone UTM du centre de la zone. emprise = (ouest, sud, est, nord)."""
    ouest, sud, est, nord = emprise
    longitude, latitude = (ouest + est) / 2, (sud + nord) / 2
    fuseau = min(60, max(1, int((longitude + 180) // 6) + 1))
    return (32600 if latitude >= 0 else 32700) + fuseau


def decrire_bande(nom, langue):
    """Retourne (capteur, 'bande' ou 'indice') pour un nom de bande de la pile."""
    prefixe, _, reste = nom.partition("_")
    cle = next(c for c, p in PREFIXES.items() if p == prefixe)
    est_indice = reste in INDICES_OPTIQUES or reste in INDICES_SAR
    return CAPTEURS[cle]["nom_court"][langue], ("indice" if est_indice else "bande")


def parametres_visu(nom_bande):
    """Paramètres d'affichage (étalement des valeurs) adaptés à une bande de la pile."""
    reste = nom_bande.partition("_")[2]
    if reste in INDICES_OPTIQUES:
        return {"min": -1, "max": 1, "palette": PALETTE_INDICE}
    if reste == "VV":
        return dict(APERCU_SAR_VV)
    if reste == "VH":
        return {"min": -30, "max": -5}
    if reste == "VH_VV":
        return {"min": -20, "max": 0}
    if reste == "RVI":
        return {"min": 0, "max": 1, "palette": PALETTE_INDICE}
    return dict(APERCU_OPTIQUE)  # réflectance


def bandes_rvb(noms_pile):
    """Trois noms de bandes (rouge, vert, bleu) d'un même capteur optique, ou None."""
    for cle in ORDRE_CAPTEURS:
        if CAPTEURS[cle]["type"] != "optique":
            continue
        p = PREFIXES[cle]
        trio = [f"{p}_red", f"{p}_green", f"{p}_blue"]
        if all(b in noms_pile for b in trio):
            return trio
    return None


# --------------------------------------------------------------------------
# Composites prétraités
# --------------------------------------------------------------------------
def composite_pretraite(cle, geometrie, configuration):
    """
    Image composite d'un capteur après prétraitement.
    Optique : bandes standard (blue, green, red, nir, swir1, swir2...) en réflectance.
    Radar   : polarisations en dB.
    """
    pre = configuration["pretraitement"]
    debut, fin = configuration["date_debut"], configuration["date_fin"]

    if CAPTEURS[cle]["type"] == "optique":
        opts = pre["optique"]
        collection = collection_optique(cle, geometrie, debut, fin,
                                        configuration["nuages_max"], options=opts)
        composite = collection.median()
        if opts["ecreter"]:
            composite = ecreter_reflectance(composite)
        if opts["combler_vides"]:
            composite = combler_vides(composite, opts["rayon_comblement_m"])
        return composite

    opts = pre["radar"]
    collection = collection_radar(geometrie, debut, fin, polarisations_necessaires(configuration),
                                  configuration["orbite"], bruit_bord=opts["bruit_bord"])
    composite = composite_radar(collection, opts["composite"])
    return filtre_speckle(composite, opts["filtre"], opts["rayon_filtre_m"])


def _url_tuiles(image, parametres):
    return image.getMapId(parametres)["tile_fetcher"].url_format


def apercus_pretraites(gdf_zone, configuration):
    """Aperçus (RVB pour l'optique, VV pour le radar) des composites prétraités."""
    geometrie = geometrie_et_tolerance(gdf_zone)[0]
    couches = []
    for cle in capteurs_actifs(configuration):
        nom = CAPTEURS[cle]["nom_court"]["fr"]
        composite = composite_pretraite(cle, geometrie, configuration).clip(geometrie)
        if CAPTEURS[cle]["type"] == "optique":
            visu = {"bands": ["red", "green", "blue"], **APERCU_OPTIQUE}
            couches.append({"nom": f"{nom} – RVB (prétraité)", "url": _url_tuiles(composite, visu),
                            "visible": len(couches) == 0})
        else:
            bande = "VV" if "VV" in polarisations_necessaires(configuration) else \
                polarisations_necessaires(configuration)[0]
            visu = {"bands": [bande], **APERCU_SAR_VV}
            couches.append({"nom": f"{nom} – {bande} (prétraité)", "url": _url_tuiles(composite, visu),
                            "visible": len(couches) == 0})
    return {"couches": couches}


# --------------------------------------------------------------------------
# Stacking
# --------------------------------------------------------------------------
def _bandes_du_capteur(cle, composite, configuration):
    """Sélectionne les bandes choisies et calcule les indices, avec le préfixe du capteur."""
    prefixe = PREFIXES[cle]
    if CAPTEURS[cle]["type"] == "optique":
        indices = [calculer_indice_optique(composite, code)
                   for code in configuration["indices_optiques"]]
        bandes = composite.select(configuration["bandes"][cle])
        noms = list(configuration["bandes"][cle]) + list(configuration["indices_optiques"])
        image = ee.Image.cat([bandes] + indices) if indices else bandes
    else:
        indices, noms_indices = [], []
        for code in configuration["indices_sar"]:  # même ordre que noms_bandes_pile()
            vv, vh = composite.select("VV"), composite.select("VH")
            if code == "VH_VV":
                indices.append(vh.subtract(vv).rename("VH_VV"))      # différence en dB
            elif code == "RVI":
                vv_lin = ee.Image(10).pow(vv.divide(10))
                vh_lin = ee.Image(10).pow(vh.divide(10))
                indices.append(vh_lin.multiply(4).divide(vv_lin.add(vh_lin)).rename("RVI"))
            noms_indices.append(code)
        bandes = composite.select(configuration["bandes"]["sentinel1"])
        noms = list(configuration["bandes"]["sentinel1"]) + noms_indices
        image = ee.Image.cat([bandes] + indices) if indices else bandes
    return image.rename([f"{prefixe}_{n}" for n in noms])


def construire_pile(gdf_zone, configuration, resolution_m):
    """
    Assemble la pile finale. Retourne un dictionnaire :
      image          : ee.Image multibande, découpée sur la zone
      bandes         : noms des bandes
      crs, echelle   : grille de travail (UTM, résolution en mètres)
      geometrie      : zone (ee.Geometry) pour les étapes suivantes
      tolerance_m    : simplification du contour utilisée pour le découpage (mètres, approx.)
      avertissement  : None ou code d'avertissement
    """
    geometrie, tolerance = geometrie_et_tolerance(
        gdf_zone, MAX_COORDONNEES_DECOUPAGE, TOLERANCES_DECOUPAGE)

    images = []
    for cle in capteurs_actifs(configuration):
        composite = composite_pretraite(cle, geometrie, configuration)
        images.append(_bandes_du_capteur(cle, composite, configuration))

    pile = ee.Image.cat(images).clip(geometrie)
    noms = noms_bandes_pile(configuration)

    # Contrôle : les bandes réellement obtenues correspondent-elles à celles prévues ?
    avertissement = None
    reelles = pile.bandNames().getInfo()
    if isinstance(reelles, list) and sorted(reelles) != sorted(noms):
        avertissement = "bandes_differentes"

    return {
        "image": pile,
        "bandes": noms,
        "crs": f"EPSG:{epsg_utm(tuple(float(v) for v in gdf_zone.total_bounds))}",
        "echelle": resolution_m,
        "geometrie": geometrie,
        "tolerance_m": round(tolerance * 111_000),
        "avertissement": avertissement,
    }


def couche_pile(pile, choix):
    """
    Couche de carte pour la pile. choix = "rvb" (couleurs naturelles) ou le nom d'une bande.
    Retourne {"nom", "url", "visible"}.
    """
    if choix == "rvb":
        trio = bandes_rvb(pile["bandes"])
        visu = {"bands": trio, **APERCU_OPTIQUE}
        nom = "Pile – RVB"
    else:
        visu = {"bands": [choix], **parametres_visu(choix)}
        nom = f"Pile – {choix}"
    return {"nom": nom, "url": _url_tuiles(pile["image"], visu), "visible": True}
