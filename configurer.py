"""
================================================================
   ASSISTANT DE CONFIGURATION — Kōtei 🍥
   Fichier : configurer.py
----------------------------------------------------------------
Script à lancer UNE SEULE FOIS EN LOCAL (sur ton ordinateur),
avant de pousser le projet sur GitHub. Il te pose les questions
une par une et écrit automatiquement le fichier .env à ta place
— tu n'as plus besoin de l'éditer à la main.

Lancement :
    python configurer.py

⚠️ Ce script sert uniquement à générer TON fichier .env local.
   Il ne fonctionne PAS sur Render (pas de terminal interactif
   disponible sur un serveur hébergé). Une fois déployé, la
   configuration se fait directement dans l'interface de Render
   (onglet "Environment" du service) — voir les explications
   fournies par Claude pour le détail du déploiement.
================================================================
"""

import os

CHEMIN_ENV = ".env"


def demander(question: str, valeur_actuelle: str = "", obligatoire: bool = False) -> str:
    """
    Pose une question dans le terminal. Si une valeur existe déjà,
    elle est proposée par défaut entre crochets (Entrée = la conserver).
    """
    suffixe = f" [{valeur_actuelle}]" if valeur_actuelle else ""
    while True:
        reponse = input(f"{question}{suffixe} : ").strip()
        if not reponse:
            reponse = valeur_actuelle
        if reponse or not obligatoire:
            return reponse
        print("   ⚠️ Cette information est obligatoire, merci de la renseigner.")


def charger_env_existant() -> dict:
    """Relit le .env existant (s'il y en a un) pour pré-remplir les réponses."""
    valeurs = {}
    if os.path.exists(CHEMIN_ENV):
        with open(CHEMIN_ENV, "r", encoding="utf-8") as fichier:
            for ligne in fichier:
                ligne = ligne.strip()
                if ligne and not ligne.startswith("#") and "=" in ligne:
                    cle, _, valeur = ligne.partition("=")
                    valeurs[cle.strip()] = valeur.strip()
    return valeurs


def main():
    print("=" * 60)
    print("  🍥  Assistant de configuration — Bot Kōtei")
    print("=" * 60)
    print("Réponds aux questions ci-dessous. Appuie sur Entrée pour")
    print("conserver une valeur déjà existante (affichée entre crochets).\n")

    valeurs = charger_env_existant()

    valeurs["DISCORD_TOKEN"] = demander(
        "🔑 Token de ton bot Discord (Developer Portal > Bot > Reset Token)",
        valeurs.get("DISCORD_TOKEN", ""),
        obligatoire=True,
    )
    valeurs["FOUNDER_IDS"] = demander(
        "👑 IDs Discord des fondateurs, séparés par des virgules (accès à !staffcheck)",
        valeurs.get("FOUNDER_IDS", ""),
    )
    valeurs["STAFF_ROLE_NAME"] = demander(
        "🛡️ Nom exact du rôle Staff sur ton serveur (accès à !resume)",
        valeurs.get("STAFF_ROLE_NAME", "Staff"),
    )
    valeurs["MODLOG_CHANNEL_ID"] = demander(
        "📋 ID du salon de logs de modération (laisser vide pour désactiver)",
        valeurs.get("MODLOG_CHANNEL_ID", ""),
    )
    valeurs["ANTHROPIC_API_KEY"] = demander(
        "🤖 Clé API Anthropic (laisser vide pour désactiver le résumé IA de !resume)",
        valeurs.get("ANTHROPIC_API_KEY", ""),
    )
    valeurs["ANTISPAM_SEUIL"] = demander(
        "🚫 Nombre de messages suspects avant sanction anti-spam",
        valeurs.get("ANTISPAM_SEUIL", "5"),
    )
    valeurs["ANTISPAM_FENETRE_SECONDES"] = demander(
        "⏱️ Fenêtre de temps observée par l'anti-spam (en secondes)",
        valeurs.get("ANTISPAM_FENETRE_SECONDES", "5"),
    )
    valeurs["ANTISPAM_MUTE_MINUTES"] = demander(
        "🔇 Durée du mute automatique anti-spam (en minutes)",
        valeurs.get("ANTISPAM_MUTE_MINUTES", "10"),
    )

    with open(CHEMIN_ENV, "w", encoding="utf-8") as fichier:
        fichier.write("# Fichier généré/mis à jour par configurer.py — ne jamais partager ni pousser sur GitHub !\n")
        for cle, valeur in valeurs.items():
            fichier.write(f"{cle}={valeur}\n")

    print("\n✅ Fichier .env écrit avec succès !")
    print("   Tu peux maintenant lancer le bot avec : python bot.py\n")


if __name__ == "__main__":
    main()
