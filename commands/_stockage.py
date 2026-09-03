"""
================================================================
   STOCKAGE DES AVERTISSEMENTS — _stockage.py
----------------------------------------------------------------
⚠️ Ce fichier commence par "_" : bot.py l'ignore lors du
   chargement automatique des Cogs. Il contient uniquement des
   fonctions de lecture/écriture du fichier data/warns.json.

⚠️ IMPORTANT SI HÉBERGÉ SUR RENDER :
   Le disque des services Render (hors "Persistent Disk" payant)
   est RÉINITIALISÉ à chaque nouveau déploiement. Les warns
   stockés ici survivent aux simples redémarrages du bot, mais
   PAS à un nouveau déploiement (git push). C'est un compromis
   accepté ici pour rester simple — voir les explications de
   Claude pour les alternatives si tu veux du 100% persistant.
================================================================
"""

import json
import os

DOSSIER_DATA = "data"
FICHIER_WARNS = os.path.join(DOSSIER_DATA, "warns.json")


def _assurer_dossier():
    """Crée le dossier data/ s'il n'existe pas encore."""
    os.makedirs(DOSSIER_DATA, exist_ok=True)


def charger_warns() -> dict:
    """
    Charge le fichier warns.json et le retourne sous forme de dict :
    { "id_serveur": { "id_membre": [ {"raison": ..., "moderateur": ..., "date": ...}, ... ] } }
    Retourne un dict vide si le fichier n'existe pas encore.
    """
    _assurer_dossier()
    if not os.path.exists(FICHIER_WARNS):
        return {}
    try:
        with open(FICHIER_WARNS, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    except (json.JSONDecodeError, OSError):
        # Fichier corrompu ou illisible : on repart sur une base vide
        # plutôt que de faire planter le bot.
        return {}


def sauvegarder_warns(donnees: dict):
    """Écrit le dict de warns dans data/warns.json (formaté et lisible)."""
    _assurer_dossier()
    with open(FICHIER_WARNS, "w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, indent=2, ensure_ascii=False)


def ajouter_warn(id_serveur: int, id_membre: int, raison: str, id_moderateur: int, date_iso: str) -> int:
    """
    Ajoute un avertissement et retourne le nombre total de warns actifs
    pour ce membre après ajout.
    """
    donnees = charger_warns()
    cle_serveur = str(id_serveur)
    cle_membre = str(id_membre)

    donnees.setdefault(cle_serveur, {})
    donnees[cle_serveur].setdefault(cle_membre, [])
    donnees[cle_serveur][cle_membre].append({
        "raison": raison,
        "moderateur": id_moderateur,
        "date": date_iso,
    })

    sauvegarder_warns(donnees)
    return len(donnees[cle_serveur][cle_membre])


def lister_warns(id_serveur: int, id_membre: int) -> list:
    """Retourne la liste des avertissements d'un membre sur un serveur."""
    donnees = charger_warns()
    return donnees.get(str(id_serveur), {}).get(str(id_membre), [])


def retirer_warn(id_serveur: int, id_membre: int, index: int) -> bool:
    """
    Retire l'avertissement à la position `index` (0 = le plus ancien).
    Retourne True si la suppression a réussi, False si l'index est invalide.
    """
    donnees = charger_warns()
    cle_serveur = str(id_serveur)
    cle_membre = str(id_membre)

    warns_membre = donnees.get(cle_serveur, {}).get(cle_membre, [])
    if index < 0 or index >= len(warns_membre):
        return False

    warns_membre.pop(index)
    sauvegarder_warns(donnees)
    return True
