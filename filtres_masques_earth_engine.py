"""
filtres_masques_earth_engine.py
-------------------------------
Rôle : les "briques" de prétraitement des images, côté Google Earth Engine :

  OPTIQUE (Landsat, Sentinel-2)
    - masque_nuages()       : nuages, ombres, cirrus, pixels défectueux (et neige en option)
    - ecreter_reflectance() : ramène les réflectances entre 0 et 1
    - combler_vides()       : comble les petits trous avec la médiane du voisinage

  RADAR (Sentinel-1)
    - masque_bruit_bord()   : retire les valeurs très basses des bords de scène
    - filtre_speckle()      : atténue le speckle (grain du radar)
    - composite_radar()     : résume plusieurs dates en une image (médiane ou moyenne)

Ce fichier ne dépend d'aucun autre fichier de l'application. Il suppose
qu'Earth Engine est déjà initialisé.

Remarque sur le radar : Google fournit Sentinel-1 déjà calibré, sans bruit
thermique et corrigé du relief (SRTM), en décibels. Le bruit de bord et le
speckle restent à traiter. Le masque de bruit de bord ci-dessous est une
approche SIMPLIFIÉE ; une chaîne complète existe (Mullissa et al., 2021,
Remote Sensing 13(10)) et pourra être ajoutée plus tard.
"""

import ee

# Bits du canal QA_PIXEL de Landsat 8/9 (niveau 2) :
# 0 remplissage, 1 nuage dilaté, 2 cirrus, 3 nuage, 4 ombre de nuage, 5 neige
BITS_LANDSAT_NUAGES = [0, 1, 2, 3, 4]
BIT_LANDSAT_NEIGE = 5

# Classes du canal SCL de Sentinel-2 :
# 1 saturé/défectueux, 3 ombre de nuage, 8 nuage (probabilité moyenne),
# 9 nuage (probabilité forte), 10 cirrus, 11 neige/glace
CLASSES_SCL_NUAGES = [1, 3, 8, 9, 10]
CLASSE_SCL_NEIGE = 11

SEUIL_BRUIT_BORD_DB = -30


# --------------------------------------------------------------------------
# Optique
# --------------------------------------------------------------------------
def masque_landsat(image, masquer_neige):
    """Image de 0/1 : 1 = pixel valide (ni nuage, ni ombre, ni cirrus, ni remplissage)."""
    bits = BITS_LANDSAT_NUAGES + ([BIT_LANDSAT_NEIGE] if masquer_neige else [])
    valeur = sum(1 << b for b in bits)
    return image.select("QA_PIXEL").bitwiseAnd(valeur).eq(0)


def masque_sentinel2(image, seuil_proba_nuage, masquer_neige):
    """Image de 0/1 : 1 = pixel valide, d'après la classification SCL et la probabilité de nuage."""
    scl = image.select("SCL")
    classes = CLASSES_SCL_NUAGES + ([CLASSE_SCL_NEIGE] if masquer_neige else [])
    masque = scl.neq(classes[0])
    for classe in classes[1:]:
        masque = masque.And(scl.neq(classe))
    return masque.And(image.select("MSK_CLDPRB").lt(seuil_proba_nuage))


def masque_nuages(cle_capteur, image, options):
    """Retourne le masque adapté au capteur, ou None si le masquage est désactivé."""
    if not options.get("masque_nuages"):
        return None
    if cle_capteur == "landsat":
        return masque_landsat(image, options["masque_neige"])
    return masque_sentinel2(image, options["proba_nuage_s2"], options["masque_neige"])


def ecreter_reflectance(image):
    """Ramène les réflectances entre 0 et 1 (les valeurs hors limites sont des artefacts)."""
    return image.clamp(0, 1)


def combler_vides(image, rayon_m):
    """
    Comble les petits trous (pixels masqués) avec la médiane des pixels voisins.
    Les pixels déjà valides ne changent pas. Les grands vides restent vides.
    """
    remplissage = image.focalMedian(rayon_m, "circle", "meters")
    return remplissage.blend(image)  # l'image d'origine est posée par-dessus


# --------------------------------------------------------------------------
# Radar
# --------------------------------------------------------------------------
def masque_bruit_bord(image):
    """Masque, bande par bande, les valeurs inférieures au seuil (en dB)."""
    return image.updateMask(image.gt(SEUIL_BRUIT_BORD_DB))


def _db_vers_lineaire(image):
    return ee.Image(10).pow(image.divide(10)).rename(image.bandNames())


def _lineaire_vers_db(image):
    return image.log10().multiply(10)


def filtre_speckle(image_db, type_filtre, rayon_m):
    """
    Atténue le speckle d'une image radar en dB.
      "mediane" : médiane focale (la médiane donne le même résultat en dB ou en linéaire)
      "moyenne" : moyenne focale calculée en linéaire (la moyenne ne doit pas se faire en dB)
      autre     : aucun filtre
    """
    if type_filtre == "mediane":
        return image_db.focalMedian(rayon_m, "circle", "meters")
    if type_filtre == "moyenne":
        lineaire = _db_vers_lineaire(image_db)
        return _lineaire_vers_db(lineaire.focalMean(rayon_m, "circle", "meters"))
    return image_db


def composite_radar(collection, type_composite):
    """Résume la collection en une image : médiane (défaut) ou moyenne calculée en linéaire."""
    if type_composite == "moyenne":
        lineaire = collection.map(_db_vers_lineaire)
        return _lineaire_vers_db(lineaire.mean())
    return collection.median()
