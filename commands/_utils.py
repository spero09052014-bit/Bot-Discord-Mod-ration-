"""
================================================================
   UTILITAIRES PARTAGÉS — _utils.py
----------------------------------------------------------------
⚠️ Ce fichier commence par "_" : bot.py l'ignore volontairement
   lors du chargement automatique des Cogs (voir bot.py). Il ne
   contient PAS de commande, seulement des fonctions réutilisées
   par plusieurs Cogs de modération.
================================================================
"""

import re
import datetime

# Table de correspondance des suffixes de durée acceptés.
UNITES = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "j": 86400,   # jour
    "d": 86400,   # day (alias anglais accepté aussi)
    "w": 604800,  # semaine
}

MOTIF_DUREE = re.compile(r"^(\d+)([smhjdw])$", re.IGNORECASE)


def parser_duree(chaine: str) -> datetime.timedelta | None:
    """
    Convertit une chaîne comme "10m", "2h", "1j" ou "1w" en timedelta.
    Retourne None si le format n'est pas reconnu.

    Exemples :
        "30s" -> 30 secondes
        "10m" -> 10 minutes
        "2h"  -> 2 heures
        "1j"  -> 1 jour
    """
    if not chaine:
        return None

    correspondance = MOTIF_DUREE.match(chaine.strip().lower())
    if not correspondance:
        return None

    quantite, unite = correspondance.groups()
    secondes = int(quantite) * UNITES[unite]

    # Discord limite les timeouts (mutes) à 28 jours maximum.
    secondes = min(secondes, 28 * 86400)

    return datetime.timedelta(seconds=secondes)
