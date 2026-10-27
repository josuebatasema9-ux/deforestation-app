"""
traductions_fr_en.py
--------------------
Rôle : contenir tous les textes de l'application en français et en anglais.
Pour ajouter un texte : l'ajouter dans "fr" ET dans "en" avec la même clé.
"""

TEXTES = {
    "fr": {
        "titre": "Détection automatique de la déforestation",
        "se_connecter": "Se connecter",
        "creer_compte": "Créer un compte",
        "email": "Adresse e-mail",
        "mot_de_passe": "Mot de passe",
        "confirmer": "Confirmer le mot de passe",
        "erreur_connexion": "E-mail ou mot de passe incorrect.",
        "erreur_email": "Adresse e-mail invalide.",
        "erreur_mdp_court": "Le mot de passe doit contenir au moins 8 caractères.",
        "erreur_mdp_different": "Les mots de passe ne correspondent pas.",
        "erreur_existe": "Ce compte existe déjà.",
        "succes_compte": "Compte créé. Vous pouvez maintenant vous connecter.",
        "deconnexion": "Se déconnecter",
        "accueil": "Accueil",
        "traitement": "Traitement",
        "tableau_bord": "Tableau de bord et rapport",
        "claire": "Claire",
        "sombre": "Sombre",
        "bouton_theme": "🎨 Thème",
        "bouton_langue": "🌐 Langue",
        "a_construire": "Cette section sera construite à une prochaine étape.",
    },
    "en": {
        "titre": "Automatic Deforestation Detection",
        "se_connecter": "Log in",
        "creer_compte": "Sign up",
        "email": "Email address",
        "mot_de_passe": "Password",
        "confirmer": "Confirm password",
        "erreur_connexion": "Incorrect email or password.",
        "erreur_email": "Invalid email address.",
        "erreur_mdp_court": "Password must be at least 8 characters.",
        "erreur_mdp_different": "Passwords do not match.",
        "erreur_existe": "This account already exists.",
        "succes_compte": "Account created. You can now log in.",
        "deconnexion": "Log out",
        "accueil": "Home",
        "traitement": "Processing",
        "tableau_bord": "Dashboard & Report",
        "claire": "Light",
        "sombre": "Dark",
        "bouton_theme": "🎨 Theme",
        "bouton_langue": "🌐 Language",
        "a_construire": "This section will be built in a later step.",
    },
}


def traduire(langue, cle):
    """Retourne le texte correspondant à la clé dans la langue choisie."""
    return TEXTES[langue][cle]
