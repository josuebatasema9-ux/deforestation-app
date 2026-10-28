"""
lecture_zone_etude.py
---------------------
Rôle : lire la ZONE D'ÉTUDE fournie par l'utilisateur sous forme de shapefile
compressé (.zip), la vérifier, la mettre en WGS84 (EPSG:4326) et calculer
quelques informations utiles (nombre d'entités, superficie, emprise).

Ce fichier ne contient AUCUN affichage : il ne fait que lire et vérifier.
L'affichage est fait dans page_traitement.py.

Un shapefile est en réalité un groupe de fichiers (.shp, .shx, .dbf, .prj...).
On les met tous dans un .zip pour les envoyer d'un seul coup.
"""

import io
import os
import tempfile
import zipfile

import geopandas as gpd

# Limites de sécurité (protègent le serveur contre les fichiers trop lourds)
TAILLE_MAX_ZIP = 50 * 1024 * 1024            # 50 Mo pour le .zip envoyé
TAILLE_MAX_DECOMPRESSEE = 300 * 1024 * 1024  # 300 Mo une fois décompressé

EXTENSIONS_UTILES = (".shp", ".shx", ".dbf", ".prj", ".cpg")


class ErreurZoneEtude(Exception):
    """Erreur de lecture. 'code' est traduit en message par la page."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def lire_zone_etude(octets_zip):
    """
    Lit un shapefile zippé et retourne un dictionnaire :
        gdf            : GeoDataFrame (géométrie seule, en EPSG:4326)
        crs_origine    : système de coordonnées d'origine (texte)
        crs_suppose    : True si le .prj manquait et qu'on a supposé WGS84
        nb_entites     : nombre de polygones
        superficie_km2 : superficie totale en km²
        emprise        : (ouest, sud, est, nord) en degrés
    Lève ErreurZoneEtude(code) si le fichier n'est pas utilisable.
    """
    if len(octets_zip) > TAILLE_MAX_ZIP:
        raise ErreurZoneEtude("trop_gros")

    try:
        archive = zipfile.ZipFile(io.BytesIO(octets_zip))
    except zipfile.BadZipFile:
        raise ErreurZoneEtude("zip_invalide")

    membres = [
        m for m in archive.infolist()
        if not m.is_dir()
        and "__MACOSX" not in m.filename
        and m.filename.lower().endswith(EXTENSIONS_UTILES)
    ]
    if sum(m.file_size for m in membres) > TAILLE_MAX_DECOMPRESSEE:
        raise ErreurZoneEtude("trop_gros")

    noms_shp = sorted(m.filename for m in membres if m.filename.lower().endswith(".shp"))
    if not noms_shp:
        raise ErreurZoneEtude("pas_de_shp")

    # On ne prend que le premier .shp et les fichiers qui portent le même nom.
    base_shp = os.path.splitext(os.path.basename(noms_shp[0]))[0].lower()

    with tempfile.TemporaryDirectory() as dossier:
        chemin_shp = None
        extensions_presentes = set()
        for membre in membres:
            nom_fichier = os.path.basename(membre.filename)  # ignore les sous-dossiers
            racine, extension = os.path.splitext(nom_fichier)
            if racine.lower() != base_shp:
                continue
            destination = os.path.join(dossier, base_shp + extension.lower())
            with archive.open(membre) as source, open(destination, "wb") as cible:
                cible.write(source.read())
            extensions_presentes.add(extension.lower())
            if extension.lower() == ".shp":
                chemin_shp = destination

        if ".dbf" not in extensions_presentes:
            raise ErreurZoneEtude("fichiers_manquants")

        # Si le .shx manque, GDAL peut le reconstruire
        os.environ.setdefault("SHAPE_RESTORE_SHX", "YES")
        try:
            gdf = gpd.read_file(chemin_shp)
        except Exception:
            raise ErreurZoneEtude("lecture_impossible")

    # --- Nettoyage : on garde uniquement les polygones valides ---
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    if gdf.empty:
        raise ErreurZoneEtude("pas_de_polygone")

    # --- Système de coordonnées ---
    crs_suppose = False
    if gdf.crs is None:
        ouest, sud, est, nord = gdf.total_bounds
        if -180 <= ouest <= 180 and -180 <= est <= 180 and -90 <= sud <= 90 and -90 <= nord <= 90:
            gdf = gdf.set_crs(epsg=4326)
            crs_suppose = True
        else:
            raise ErreurZoneEtude("crs_absent")
    crs_origine = gdf.crs.to_string()

    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf.geometry.make_valid()
    gdf = gdf[["geometry"]].reset_index(drop=True)

    # --- Superficie en km² (calculée dans une projection métrique adaptée) ---
    gdf_metrique = gdf.to_crs(gdf.estimate_utm_crs())
    superficie_km2 = float(gdf_metrique.geometry.area.sum() / 1_000_000)

    ouest, sud, est, nord = (float(v) for v in gdf.total_bounds)
    return {
        "gdf": gdf,
        "crs_origine": crs_origine,
        "crs_suppose": crs_suppose,
        "nb_entites": int(len(gdf)),
        "superficie_km2": superficie_km2,
        "emprise": (ouest, sud, est, nord),
    }
