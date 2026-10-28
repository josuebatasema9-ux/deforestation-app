"""
connexion_earth_engine.py
-------------------------
Rôle : connecter l'application à Google Earth Engine (GEE).

Deux façons de se connecter, choisies automatiquement :

 1. COMPTE DE SERVICE (pour l'application en ligne, Streamlit Cloud, et aussi
    possible en local) : si les "secrets" Streamlit contiennent une section
    [earthengine], on l'utilise. La clé n'est JAMAIS écrite dans le code.

 2. COMPTE PERSONNEL (pour le travail en local) : on utilise l'authentification
    faite une fois dans le terminal (ee.Authenticate) et l'identifiant de votre
    projet Google Cloud saisi dans l'application.

La fonction principale retourne (ok, code, detail). Le "code" est traduit en
message lisible par outils_donnees_satellitaires.py.
"""

import os

import streamlit as st

PORTEE_EARTH_ENGINE = ["https://www.googleapis.com/auth/earthengine"]


def lire_compte_service():
    """Retourne les informations du compte de service (secrets Streamlit), ou None."""
    try:
        if "earthengine" in st.secrets:
            return dict(st.secrets["earthengine"])
    except Exception:
        pass  # pas de fichier secrets : situation normale en local
    return None


def initialiser_earth_engine(projet_id=""):
    """
    Initialise Earth Engine puis fait un petit test réel de connexion.
    Retourne (ok, code, detail) avec code parmi :
      "ok_compte_service", "ok_local", "ee_absent", "projet_requis",
      "non_authentifie", "erreur"
    """
    try:
        import ee
    except ImportError:
        return False, "ee_absent", ""

    compte = lire_compte_service()
    try:
        if compte:
            from google.oauth2 import service_account

            identifiants = service_account.Credentials.from_service_account_info(
                compte, scopes=PORTEE_EARTH_ENGINE
            )
            projet = compte.get("project_id", "")
            ee.Initialize(identifiants, project=projet)
            code_ok = "ok_compte_service"
        else:
            projet = (projet_id or os.environ.get("EE_PROJECT", "")).strip()
            if not projet:
                return False, "projet_requis", ""
            ee.Initialize(project=projet)
            code_ok = "ok_local"

        # Test réel : une opération minuscule exécutée par les serveurs de Google.
        # Elle échoue si le projet n'est pas enregistré pour Earth Engine.
        ee.Number(1).getInfo()
        return True, code_ok, projet

    except Exception as erreur:
        texte = str(erreur)
        lettres = texte.lower()
        if compte is None and (
            "authenticate" in lettres or "credentials" in lettres or "authorize" in lettres
        ):
            return False, "non_authentifie", texte[:300]
        return False, "erreur", texte[:300]
