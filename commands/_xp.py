"""
================================================================
   STOCKAGE & CALCUL DE L'XP — _xp.py
----------------------------------------------------------------
⚠️ Fichier utilitaire (préfixé "_") : ignoré par le chargeur
   automatique de Cogs dans bot.py.

Gère la persistance de l'expérience (XP) des membres dans
data/niveaux.json, et le calcul du niveau à partir de l'XP.

⚠️ Comme pour warns.json, ce fichier est réinitialisé à chaque
   nouveau déploiement sur Render (disque non persistant hors
   offre payante).
================================================================
"""

import json
import os

DOSSIER_DATA = "data"
FICHIER_NIVEAUX = os.path.join(DOSSIER_DATA, "niveaux.json")


def _assurer_dossier():
    os.makedirs(DOSSIER_DATA, exist_ok=True)


def charger_niveaux() -> dict:
    _assurer_dossier()
    if not os.path.exists(FICHIER_NIVEAUX):
        return {}
    try:
        with open(FICHIER_NIVEAUX, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    except (json.JSONDecodeError, OSError):
        return {}


def sauvegarder_niveaux(donnees: dict):
    _assurer_dossier()
    with open(FICHIER_NIVEAUX, "w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, indent=2, ensure_ascii=False)


def xp_necessaire_pour(niveau: int) -> int:
    """Chaque niveau demande un peu plus d'XP que le précédent."""
    return 5 * (niveau ** 2) + 50 * niveau + 100


def niveau_depuis_xp(xp_total: int) -> int:
    """Convertit un total d'XP cumulé en niveau atteint."""
    niveau = 0
    xp_cumule = 0
    while True:
        xp_cumule += xp_necessaire_pour(niveau)
        if xp_total < xp_cumule:
            return niveau
        niveau += 1


def ajouter_xp(id_serveur: int, id_membre: int, montant: int) -> tuple[int, int, bool]:
    """
    Ajoute de l'XP à un membre.
    Retourne (nouveau_total_xp, nouveau_niveau, a_level_up).
    """
    donnees = charger_niveaux()
    cle_serveur = str(id_serveur)
    cle_membre = str(id_membre)

    donnees.setdefault(cle_serveur, {})
    ancien_xp = donnees[cle_serveur].get(cle_membre, 0)
    ancien_niveau = niveau_depuis_xp(ancien_xp)

    nouveau_xp = ancien_xp + montant
    nouveau_niveau = niveau_depuis_xp(nouveau_xp)

    donnees[cle_serveur][cle_membre] = nouveau_xp
    sauvegarder_niveaux(donnees)

    return nouveau_xp, nouveau_niveau, nouveau_niveau > ancien_niveau


def obtenir_xp(id_serveur: int, id_membre: int) -> int:
    donnees = charger_niveaux()
    return donnees.get(str(id_serveur), {}).get(str(id_membre), 0)


def classement(id_serveur: int, limite: int = 10) -> list[tuple[str, int]]:
    """Retourne les [(id_membre, xp), ...] triés du plus haut au plus bas."""
    donnees = charger_niveaux().get(str(id_serveur), {})
    return sorted(donnees.items(), key=lambda item: item[1], reverse=True)[:limite]
