"""
================================================================
   CONFIGURATION PAR SERVEUR — _config.py
----------------------------------------------------------------
⚠️ Ce fichier commence par "_" : bot.py l'ignore lors du
   chargement automatique des Cogs.

Ce module remplace le besoin de modifier le fichier .env à la
main pour tout ce qui concerne UN serveur en particulier (salon
de logs, salon de bienvenue, rôle staff, seuils anti-spam...).

Tout se règle maintenant en tapant /config directement dans un
salon Discord, en cliquant sur des menus déroulants — voir
commands/config.py pour l'interface.

Les réglages sont stockés dans data/config.json, au format :
{
  "id_du_serveur": {
      "MODLOG_CHANNEL_ID": "123...",
      "STAFF_ROLE_ID": "456...",
      ...
  }
}

Priorité de lecture d'un réglage (voir obtenir_reglage) :
    1. Valeur définie via /config sur CE serveur (data/config.json)
    2. Sinon, valeur du fichier .env (réglage global de secours,
       pratique pour ne configurer qu'un seul serveur au départ)
    3. Sinon, valeur par défaut codée en dur

⚠️ MÊME AVERTISSEMENT QUE POUR warns.json (_stockage.py) : sur
   Render, hors "Persistent Disk" payant, ce fichier est
   réinitialisé à chaque nouveau déploiement (git push), mais
   survit aux simples redémarrages du bot.
================================================================
"""

import json
import os

DOSSIER_DATA = "data"
FICHIER_CONFIG = os.path.join(DOSSIER_DATA, "config.json")

# Valeur par défaut "en dur" de chaque réglage, utilisée si absente
# à la fois de config.json (serveur) et du .env (global).
REGLAGES_PAR_DEFAUT = {
    "STAFF_ROLE_ID": "",
    "MODLOG_CHANNEL_ID": "",
    "WELCOME_CHANNEL_ID": "",
    "AUTOROLE_ID": "",
    "SUGGESTIONS_CHANNEL_ID": "",
    "TICKETS_CATEGORY_ID": "",
    "FOUNDER_IDS": "",
    "ANTISPAM_SEUIL": "5",
    "ANTISPAM_FENETRE_SECONDES": "5",
    "ANTISPAM_MUTE_MINUTES": "10",
    "XP_PAR_MESSAGE": "15",
    "XP_COOLDOWN_SECONDES": "60",
}

# Libellés lisibles utilisés par l'interface /config et par !config-voir.
LIBELLES = {
    "STAFF_ROLE_ID": "🛡️ Rôle Staff",
    "MODLOG_CHANNEL_ID": "📋 Salon de logs de modération",
    "WELCOME_CHANNEL_ID": "👋 Salon de bienvenue / au revoir",
    "AUTOROLE_ID": "🎭 Rôle automatique (nouveaux membres)",
    "SUGGESTIONS_CHANNEL_ID": "💡 Salon des suggestions",
    "TICKETS_CATEGORY_ID": "🎫 Catégorie des tickets",
    "FOUNDER_IDS": "👑 Fondateurs (accès à /staffcheck)",
    "ANTISPAM_SEUIL": "🚫 Seuil anti-spam (messages)",
    "ANTISPAM_FENETRE_SECONDES": "⏱️ Fenêtre anti-spam (secondes)",
    "ANTISPAM_MUTE_MINUTES": "🔇 Durée du mute anti-spam (minutes)",
    "XP_PAR_MESSAGE": "📈 XP par message",
    "XP_COOLDOWN_SECONDES": "⏱️ Cooldown XP (secondes)",
}


def _assurer_dossier():
    os.makedirs(DOSSIER_DATA, exist_ok=True)


def _charger_tout() -> dict:
    _assurer_dossier()
    if not os.path.exists(FICHIER_CONFIG):
        return {}
    try:
        with open(FICHIER_CONFIG, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    except (json.JSONDecodeError, OSError):
        # Fichier corrompu ou illisible : on repart sur une base vide
        # plutôt que de faire planter le bot.
        return {}


def _sauvegarder_tout(donnees: dict):
    _assurer_dossier()
    with open(FICHIER_CONFIG, "w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, indent=2, ensure_ascii=False)


def obtenir_config_serveur(id_serveur: int) -> dict:
    """Retourne le dict complet de réglages définis via /config pour ce serveur."""
    return _charger_tout().get(str(id_serveur), {})


def definir_reglage(id_serveur: int, cle: str, valeur: str):
    """
    Définit un réglage pour un serveur donné. Passer une valeur vide ("")
    revient à désactiver/effacer ce réglage (retour à l'éventuelle valeur
    du .env, ou à la valeur par défaut).
    """
    donnees = _charger_tout()
    cle_serveur = str(id_serveur)
    donnees.setdefault(cle_serveur, {})
    if valeur:
        donnees[cle_serveur][cle] = str(valeur)
    else:
        donnees[cle_serveur].pop(cle, None)
    _sauvegarder_tout(donnees)


def obtenir_reglage(id_serveur: int, cle: str) -> str:
    """
    Lit un réglage en respectant la priorité :
    config.json (serveur, via /config) > .env (global) > valeur par défaut.
    """
    config_serveur = obtenir_config_serveur(id_serveur)
    if config_serveur.get(cle):
        return config_serveur[cle]
    valeur_env = os.getenv(cle, "")
    if valeur_env:
        return valeur_env
    return REGLAGES_PAR_DEFAUT.get(cle, "")


def obtenir_reglage_int(id_serveur: int, cle: str) -> int:
    """Comme obtenir_reglage, mais renvoie directement un entier."""
    try:
        return int(obtenir_reglage(id_serveur, cle))
    except (TypeError, ValueError):
        return int(REGLAGES_PAR_DEFAUT.get(cle, "0") or "0")


def obtenir_founder_ids(id_serveur: int) -> set:
    """Renvoie l'ensemble des IDs fondateurs (config serveur + .env combinés)."""
    brut = obtenir_reglage(id_serveur, "FOUNDER_IDS")
    return {
        int(id_str.strip())
        for id_str in brut.split(",")
        if id_str.strip().isdigit()
    }
