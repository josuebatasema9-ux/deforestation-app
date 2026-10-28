"""
catalogue_capteurs_indices.py
-----------------------------
Rôle : décrire les CAPTEURS satellitaires disponibles (Landsat 8/9, Sentinel-2,
Sentinel-1), leurs BANDES et les INDICES SPECTRAUX proposés à l'utilisateur.

Ce fichier ne contient que des données (pas de calcul, pas d'affichage).
Pour ajouter un indice : l'ajouter dans INDICES_OPTIQUES avec sa formule.

Sources des identifiants, noms de bandes et facteurs d'échelle : catalogue de
données Google Earth Engine (developers.google.com/earth-engine/datasets).
"""

# Noms "standard" des bandes optiques utilisés partout dans l'application.
# Landsat et Sentinel-2 sont renommés vers ces noms : le reste du code (indices,
# stacking) fonctionne alors de la même façon pour les deux capteurs.
BANDES_OPTIQUES_LIBELLES = {
    "blue": {"fr": "Bleu", "en": "Blue"},
    "green": {"fr": "Vert", "en": "Green"},
    "red": {"fr": "Rouge", "en": "Red"},
    "nir": {"fr": "Proche infrarouge (NIR)", "en": "Near infrared (NIR)"},
    "swir1": {"fr": "Infrarouge moyen 1 (SWIR1)", "en": "Shortwave infrared 1 (SWIR1)"},
    "swir2": {"fr": "Infrarouge moyen 2 (SWIR2)", "en": "Shortwave infrared 2 (SWIR2)"},
    "rededge1": {"fr": "Bord du rouge 1", "en": "Red edge 1"},
    "rededge2": {"fr": "Bord du rouge 2", "en": "Red edge 2"},
    "rededge3": {"fr": "Bord du rouge 3", "en": "Red edge 3"},
}

# Bandes nécessaires au calcul des indices (toujours chargées, même si non cochées)
BANDES_COEUR = ["blue", "green", "red", "nir", "swir1", "swir2"]

CAPTEURS = {
    "landsat": {
        "type": "optique",
        "nom": {"fr": "Landsat 8/9 (optique, 30 m)", "en": "Landsat 8/9 (optical, 30 m)"},
        "nom_court": {"fr": "Landsat 8/9", "en": "Landsat 8/9"},
        # Collection 2, niveau 2 (réflectance de surface), Tier 1
        "collections": ["LANDSAT/LC08/C02/T1_L2", "LANDSAT/LC09/C02/T1_L2"],
        "propriete_nuages": "CLOUD_COVER",
        # nom standard -> nom de la bande dans Earth Engine
        "bandes": {
            "blue": "SR_B2", "green": "SR_B3", "red": "SR_B4",
            "nir": "SR_B5", "swir1": "SR_B6", "swir2": "SR_B7",
        },
        # réflectance = valeur × échelle + décalage
        "echelle": 0.0000275,
        "decalage": -0.2,
        "date_min": "2013-03-18",  # début de Landsat 8
    },
    "sentinel2": {
        "type": "optique",
        "nom": {"fr": "Sentinel-2 (optique, 10-20 m)", "en": "Sentinel-2 (optical, 10-20 m)"},
        "nom_court": {"fr": "Sentinel-2", "en": "Sentinel-2"},
        # Réflectance de surface harmonisée (cohérente avant/après 2022)
        "collections": ["COPERNICUS/S2_SR_HARMONIZED"],
        "propriete_nuages": "CLOUDY_PIXEL_PERCENTAGE",
        "bandes": {
            "blue": "B2", "green": "B3", "red": "B4", "nir": "B8",
            "swir1": "B11", "swir2": "B12",
            "rededge1": "B5", "rededge2": "B6", "rededge3": "B7",
        },
        "echelle": 0.0001,
        "decalage": 0.0,
        "date_min": "2017-03-28",
    },
    "sentinel1": {
        "type": "radar",
        "nom": {"fr": "Sentinel-1 (radar SAR, 10 m)", "en": "Sentinel-1 (SAR radar, 10 m)"},
        "nom_court": {"fr": "Sentinel-1", "en": "Sentinel-1"},
        # Données déjà corrigées (bruit thermique, calibration, relief) et en décibels
        "collections": ["COPERNICUS/S1_GRD"],
        "bandes": ["VV", "VH"],
        "date_min": "2014-10-03",
    },
}

# --------------------------------------------------------------------------
# Indices spectraux optiques.
# Les formules utilisent les variables BLUE, GREEN, RED, NIR, SWIR1, SWIR2
# (réflectances entre 0 et 1) et la syntaxe d'Earth Engine (image.expression).
# --------------------------------------------------------------------------
INDICES_OPTIQUES = {
    "NDVI": {
        "formule": "(NIR - RED) / (NIR + RED)",
        "fr": "Végétation (vigueur de la végétation)",
        "en": "Vegetation (vegetation vigor)",
    },
    "EVI": {
        "formule": "2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1)",
        "fr": "Végétation améliorée (moins sensible à l'atmosphère)",
        "en": "Enhanced vegetation (less sensitive to atmosphere)",
    },
    "SAVI": {
        "formule": "1.5 * (NIR - RED) / (NIR + RED + 0.5)",
        "fr": "Végétation ajustée au sol (zones clairsemées)",
        "en": "Soil-adjusted vegetation (sparse areas)",
    },
    "GNDVI": {
        "formule": "(NIR - GREEN) / (NIR + GREEN)",
        "fr": "Végétation verte (sensible à la chlorophylle)",
        "en": "Green vegetation (chlorophyll sensitive)",
    },
    "NBR": {
        "formule": "(NIR - SWIR2) / (NIR + SWIR2)",
        "fr": "Rapport de brûlure (feux, perturbations forestières)",
        "en": "Burn ratio (fires, forest disturbance)",
    },
    "NDMI": {
        "formule": "(NIR - SWIR1) / (NIR + SWIR1)",
        "fr": "Humidité de la végétation",
        "en": "Vegetation moisture",
    },
    "NDWI": {
        "formule": "(GREEN - NIR) / (GREEN + NIR)",
        "fr": "Eau (McFeeters)",
        "en": "Water (McFeeters)",
    },
    "MNDWI": {
        "formule": "(GREEN - SWIR1) / (GREEN + SWIR1)",
        "fr": "Eau modifié (distingue l'eau du bâti)",
        "en": "Modified water (separates water from built-up)",
    },
    "NDBI": {
        "formule": "(SWIR1 - NIR) / (SWIR1 + NIR)",
        "fr": "Surfaces bâties",
        "en": "Built-up areas",
    },
    "BSI": {
        "formule": "((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))",
        "fr": "Sol nu",
        "en": "Bare soil",
    },
}

# --------------------------------------------------------------------------
# Indices radar (Sentinel-1). Les valeurs VV et VH sont en décibels (dB).
#   VH_VV : différence VH - VV en dB (équivaut au rapport VH/VV en linéaire)
#   RVI   : Radar Vegetation Index = 4·VH / (VV + VH), calculé en linéaire
# --------------------------------------------------------------------------
INDICES_SAR = {
    "VH_VV": {
        "fr": "Rapport VH/VV (en dB)",
        "en": "VH/VV ratio (in dB)",
    },
    "RVI": {
        "fr": "Indice radar de végétation (RVI)",
        "en": "Radar Vegetation Index (RVI)",
    },
}

# Valeurs de réflectance par défaut pour l'aperçu en couleurs naturelles
APERCU_OPTIQUE = {"min": 0.0, "max": 0.3}
APERCU_SAR_VV = {"min": -25, "max": 0}
