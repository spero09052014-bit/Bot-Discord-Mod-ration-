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

⚠️ Ce script sert uniquement à générer TON fichier .env local,
   et ne concerne que les réglages GLOBAUX du bot (secrets +
   comportement de secours si aucun serveur n'a encore configuré
   /config). Il ne fonctionne PAS sur Render (pas de terminal
   interactif disponible sur un serveur hébergé). Une fois
   déployé, ces réglages se font dans l'interface de Render
   (onglet "Environment" du service).

✅ TOUT LE RESTE (salon de logs, salon de bienvenue, rôle Staff,
   fondateurs, seuils anti-spam, XP...) se configure directement
   dans Discord avec la commande /config — 100% cliquable, sans
   toucher au code ni au .env, et modifiable à tout moment par
   n'importe quel administrateur du serveur.
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
    print("ℹ️  Seuls les réglages globaux/sensibles sont demandés ici.")
    print("    Tout le reste (salons, rôles, seuils...) se configure")
    print("    ensuite avec /config directement dans Discord.\n")

    valeurs = charger_env_existant()

    valeurs["DISCORD_TOKEN"] = demander(
        "🔑 Token de ton bot Discord (Developer Portal > Bot > Reset Token)",
        valeurs.get("DISCORD_TOKEN", ""),
        obligatoire=True,
    )
    valeurs["SERVEUR_ID"] = demander(
        "🏠 ID de ton serveur Discord (pour synchroniser les commandes / instantanément, sinon vide = jusqu'à 1h de délai)",
        valeurs.get("SERVEUR_ID", ""),
    )
    valeurs["ANTHROPIC_API_KEY"] = demander(
        "🤖 Clé API Anthropic (laisser vide pour désactiver le résumé IA de !resume)",
        valeurs.get("ANTHROPIC_API_KEY", ""),
    )

    with open(CHEMIN_ENV, "w", encoding="utf-8") as fichier:
        fichier.write("# Fichier généré/mis à jour par configurer.py — ne jamais partager ni pousser sur GitHub !\n")
        for cle, valeur in valeurs.items():
            fichier.write(f"{cle}={valeur}\n")

    print("\n✅ Fichier .env écrit avec succès !")
    print("   Tu peux maintenant lancer le bot avec : python bot.py")
    print("   Puis tape /config sur ton serveur Discord pour tout régler en cliquant. 🍥\n")


if __name__ == "__main__":
    main()
