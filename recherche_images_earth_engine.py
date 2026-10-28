"""
recherche_images_earth_engine.py
--------------------------------
Rôle : interroger Google Earth Engine pour
  - trouver les images disponibles (zone + dates + nuages + capteur),
  - compter les images,
  - préparer des APERÇUS (composites médians) affichables sur la carte.

Ce fichier ne contient AUCUN affichage Streamlit. Il suppose qu'Earth Engine
est déjà initialisé (voir connexion_earth_engine.py).

Les images optiques (Landsat, Sentinel-2) sont converties en réflectance
(0 à 1) et leurs bandes sont renommées avec les noms standard du catalogue.
Le calcul des indices et le stacking final seront faits à l'étape 5c.
"""

import ee

from filtres_masques_earth_engine import masque_bruit_bord, masque_nuages
from catalogue_capteurs_indices import (
    APERCU_OPTIQUE,
    APERCU_SAR_VV,
    BANDES_COEUR,
    CAPTEURS,
    INDICES_OPTIQUES,
)

PALETTE_INDICE = ["#a50026", "#f46d43", "#fee08b", "#d9ef8b", "#66bd63", "#006837"]
NB_MAX_INDICES_APERCU = 3
MAX_COORDONNEES_ENVOI = 5000  # au-delà, la zone est simplifiée avant envoi à Google


# --------------------------------------------------------------------------
# Zone d'étude -> géométrie Earth Engine
# --------------------------------------------------------------------------
TOLERANCES_RECHERCHE = (0, 0.0005, 0.002, 0.01)  # degrés (0,0005° ≈ 50 m)


def geometrie_et_tolerance(gdf, max_coordonnees=MAX_COORDONNEES_ENVOI,
                           tolerances=TOLERANCES_RECHERCHE):
    """
    Fusionne les polygones de la zone et les simplifie si nécessaire (Google limite
    la taille des requêtes). Retourne (géométrie Earth Engine, tolérance utilisée en degrés).
    Pour la recherche d'images, une simplification allant jusqu'à ~1 km est sans
    importance. Pour le découpage final, on utilise des tolérances beaucoup plus fines.
    """
    from shapely import get_num_coordinates
    from shapely.geometry import mapping

    try:
        union = gdf.geometry.union_all()
    except AttributeError:  # anciennes versions de geopandas
        union = gdf.geometry.unary_union

    for tolerance in tolerances:
        forme = union if tolerance == 0 else union.simplify(tolerance, preserve_topology=True)
        if get_num_coordinates(forme) <= max_coordonnees:
            break
    return ee.Geometry(mapping(forme)), tolerance


def geometrie_pour_earth_engine(gdf):
    """Version simple : la géométrie seule (utilisée pour la recherche d'images)."""
    return geometrie_et_tolerance(gdf)[0]


# --------------------------------------------------------------------------
# Collections d'images
# --------------------------------------------------------------------------
def _fin_exclusive(date_fin):
    """Earth Engine exclut la date de fin : on ajoute un jour pour l'inclure."""
    return ee.Date(date_fin.isoformat()).advance(1, "day")


def _preparer_optique(cle, options=None):
    """
    Retourne une fonction qui convertit une image en réflectance + noms standard.
    Si "options" est fourni (prétraitement), les pixels de nuages/ombres sont masqués.
    """
    capteur = CAPTEURS[cle]
    noms_standard = list(capteur["bandes"].keys())
    noms_gee = [capteur["bandes"][n] for n in noms_standard]

    def fonction(image):
        reflectance = (
            image.select(noms_gee)
            .multiply(capteur["echelle"])
            .add(capteur["decalage"])
            .rename(noms_standard)
        )
        if options:
            masque = masque_nuages(cle, image, options)  # utilise les canaux QA / SCL
            if masque is not None:
                reflectance = reflectance.updateMask(masque)
        return reflectance.copyProperties(image, ["system:time_start"])

    return fonction


def collection_optique(cle, geometrie, date_debut, date_fin, nuages_max, options=None):
    """Images Landsat 8/9 ou Sentinel-2 filtrées (zone, dates, % de nuages) ; masquées si options."""
    capteur = CAPTEURS[cle]
    collection = None
    for identifiant in capteur["collections"]:
        partie = (
            ee.ImageCollection(identifiant)
            .filterBounds(geometrie)
            .filterDate(ee.Date(date_debut.isoformat()), _fin_exclusive(date_fin))
            .filter(ee.Filter.lt(capteur["propriete_nuages"], nuages_max))
        )
        collection = partie if collection is None else collection.merge(partie)
    return collection.map(_preparer_optique(cle, options))


def collection_radar(geometrie, date_debut, date_fin, polarisations, orbite, bruit_bord=False):
    """Images Sentinel-1 (mode IW) contenant les polarisations demandées."""
    collection = (
        ee.ImageCollection(CAPTEURS["sentinel1"]["collections"][0])
        .filterBounds(geometrie)
        .filterDate(ee.Date(date_debut.isoformat()), _fin_exclusive(date_fin))
        .filter(ee.Filter.eq("instrumentMode", "IW"))
    )
    # transmitterReceiverPolarisation est une LISTE : on utilise listContains
    for polarisation in polarisations:
        collection = collection.filter(
            ee.Filter.listContains("transmitterReceiverPolarisation", polarisation)
        )
    if orbite in ("ASCENDING", "DESCENDING"):
        collection = collection.filter(ee.Filter.eq("orbitProperties_pass", orbite))
    collection = collection.select(list(polarisations))
    if bruit_bord:
        collection = collection.map(masque_bruit_bord)
    return collection


# --------------------------------------------------------------------------
# Indices (utilisés pour les aperçus ; le stacking complet viendra à l'étape 5c)
# --------------------------------------------------------------------------
def calculer_indice_optique(image, code_indice):
    """Calcule un indice spectral à partir des bandes standard (réflectances)."""
    variables = {
        "BLUE": image.select("blue"), "GREEN": image.select("green"),
        "RED": image.select("red"), "NIR": image.select("nir"),
        "SWIR1": image.select("swir1"), "SWIR2": image.select("swir2"),
    }
    return image.expression(INDICES_OPTIQUES[code_indice]["formule"], variables).rename(code_indice)


# --------------------------------------------------------------------------
# Recherche complète : comptage + aperçus
# --------------------------------------------------------------------------
def _url_tuiles(image, parametres_visu):
    """Demande à Earth Engine l'adresse des tuiles d'une image (pour la carte)."""
    identifiant = image.getMapId(parametres_visu)
    return identifiant["tile_fetcher"].url_format


def rechercher_images(gdf_zone, configuration):
    """
    Cherche les images pour chaque capteur choisi.
    Retourne {"nb": {capteur: nombre d'images}, "couches": [couches de carte]}.
    Chaque couche : {"nom": ..., "url": ..., "visible": bool}.
    """
    geometrie = geometrie_pour_earth_engine(gdf_zone)
    debut, fin = configuration["date_debut"], configuration["date_fin"]
    nombres, couches = {}, []

    for cle, capteur in CAPTEURS.items():
        if not configuration["capteurs"].get(cle):
            continue
        nom = capteur["nom_court"]["fr"]

        if capteur["type"] == "optique":
            collection = collection_optique(cle, geometrie, debut, fin, configuration["nuages_max"])
            nombres[cle] = int(collection.size().getInfo())
            if nombres[cle] == 0:
                continue
            composite = collection.median().clip(geometrie)
            visu = {"bands": ["red", "green", "blue"], **APERCU_OPTIQUE}
            couches.append({"nom": f"{nom} – RVB", "url": _url_tuiles(composite, visu),
                            "visible": len(couches) == 0})
            for code in configuration["indices_optiques"][:NB_MAX_INDICES_APERCU]:
                indice = calculer_indice_optique(composite, code)
                visu = {"min": -1, "max": 1, "palette": PALETTE_INDICE}
                couches.append({"nom": f"{nom} – {code}", "url": _url_tuiles(indice, visu),
                                "visible": False})

        else:  # radar
            polarisations = set(configuration["bandes"]["sentinel1"])
            if configuration["indices_sar"]:
                polarisations |= {"VV", "VH"}  # les indices radar ont besoin des deux
            polarisations = sorted(polarisations)
            collection = collection_radar(geometrie, debut, fin, polarisations,
                                          configuration["orbite"])
            nombres[cle] = int(collection.size().getInfo())
            if nombres[cle] == 0:
                continue
            composite = collection.median().clip(geometrie)
            bande = "VV" if "VV" in polarisations else polarisations[0]
            visu = {"bands": [bande], **APERCU_SAR_VV}
            couches.append({"nom": f"{nom} – {bande} (dB)", "url": _url_tuiles(composite, visu),
                            "visible": len(couches) == 0})

    return {"nb": nombres, "couches": couches}
