"""
================================================================
   BOT DISCORD — Kōtei 🍥
   Fichier principal : bot.py
----------------------------------------------------------------
Ce fichier est le "cœur" du bot. Il ne contient AUCUNE commande
directement : son unique rôle est de :

    1. Charger les variables sensibles depuis le fichier .env
    2. Configurer les Intents (permissions d'écoute Discord)
    3. Charger AUTOMATIQUEMENT tous les fichiers .py présents
       dans le dossier "commands/" (nos Cogs = modules de commandes)
    4. Démarrer le bot avec le token Discord

=> POUR AJOUTER UNE NOUVELLE COMMANDE :
   Crée un nouveau fichier .py dans "commands/", respecte le format
   d'un Cog (voir ping.py comme modèle minimal), et c'est tout !
   AUCUNE modification de ce fichier n'est nécessaire.
================================================================
"""

import os
import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Mini serveur web (Flask) répondant aux pings d'UptimeRobot, pour
# empêcher Render de mettre le bot en veille (voir keep_alive.py).
from keep_alive import demarrer_keep_alive

# ----------------------------------------------------------------
# 1. CHARGEMENT DES VARIABLES D'ENVIRONNEMENT (.env)
# ----------------------------------------------------------------
# load_dotenv() lit le fichier ".env" situé à la racine du projet
# et injecte automatiquement son contenu dans les variables
# d'environnement du système (os.environ). Le token n'apparaît
# ainsi JAMAIS en clair dans le code source (donc jamais sur GitHub).
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN or TOKEN == "METS_TON_TOKEN_ICI":
    raise RuntimeError(
        "❌ Aucun token valide trouvé ! Ouvre le fichier .env à la racine "
        "du projet et remplace 'METS_TON_TOKEN_ICI' par ton vrai token Discord."
    )

# ----------------------------------------------------------------
# 2. CONFIGURATION DU LOGGING (pour voir clairement ce qu'il se passe)
# ----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("Kotei")

# ----------------------------------------------------------------
# 3. CONFIGURATION DES INTENTS (permissions d'écoute Discord)
# ----------------------------------------------------------------
# Les Intents indiquent à Discord quels types d'événements le bot
# souhaite recevoir. Certains sont "privilégiés" et DOIVENT être
# activés manuellement dans le Developer Portal (voir les
# instructions de fin de message).
intents = discord.Intents.default()
intents.message_content = True   # Obligatoire pour lire le texte des messages (!ping, !clear, etc.)
intents.members = True           # Obligatoire pour récupérer la liste des membres (staffcheck, mentions...)
intents.moderation = True        # Obligatoire pour les événements liés aux bans/kicks et à l'Audit Log

# ----------------------------------------------------------------
# 4. CRÉATION DE L'INSTANCE DU BOT
# ----------------------------------------------------------------
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=commands.DefaultHelpCommand(),
)

# Dossier contenant les Cogs (commandes) à charger automatiquement.
COMMANDS_FOLDER = "commands"


@bot.event
async def on_ready():
    """
    Déclenché une fois que le bot est bien connecté à Discord.
    On en profite pour définir son statut personnalisé.
    """
    # Statut affiché : "Regarde Surveiller Kōtei 🍥" (activité de type "Watching")
    activite = discord.Activity(
        type=discord.ActivityType.watching,
        name="Surveiller Kōtei 🍥",
    )
    await bot.change_presence(status=discord.Status.online, activity=activite)

    log.info(f"✅ Connecté en tant que {bot.user} (ID: {bot.user.id})")
    log.info("✅ Statut personnalisé défini : Surveiller Kōtei 🍥")
    log.info(f"✅ {len(bot.cogs)} Cog(s) actif(s) : {', '.join(bot.cogs.keys()) or 'aucun'}")


async def charger_les_cogs():
    """
    Parcourt le dossier "commands/" et charge automatiquement tous
    les fichiers .py trouvés en tant qu'extensions (Cogs).

    C'est LE mécanisme qui permet d'ajouter une commande simplement
    en déposant un fichier dans le dossier : chaque fichier .py
    devient un module de commandes totalement indépendant.
    """
    if not os.path.isdir(COMMANDS_FOLDER):
        log.warning(f"⚠️ Le dossier '{COMMANDS_FOLDER}/' est introuvable, aucune commande chargée.")
        return

    for nom_fichier in sorted(os.listdir(COMMANDS_FOLDER)):
        # On ignore tout ce qui n'est pas un fichier Python "normal"
        # (les fichiers commençant par "_" comme __init__.py, __pycache__, etc.)
        if not nom_fichier.endswith(".py") or nom_fichier.startswith("_"):
            continue

        nom_module = nom_fichier[:-3]  # on retire l'extension ".py"
        chemin_extension = f"{COMMANDS_FOLDER}.{nom_module}"

        try:
            await bot.load_extension(chemin_extension)
            log.info(f"🔌 Cog chargé avec succès : {nom_module}")
        except Exception as erreur:
            # Si UN fichier contient une erreur, les autres Cogs se
            # chargent quand même : un bug n'en bloque pas un autre.
            log.error(f"❌ Impossible de charger le Cog '{nom_module}' : {erreur}")


async def main():
    """
    Point d'entrée principal :
      1. On démarre le mini serveur web (pour UptimeRobot / Render)
      2. On charge les Cogs
      3. On démarre le bot Discord
    """
    demarrer_keep_alive()
    log.info("🌐 Mini serveur web keep_alive démarré (pour UptimeRobot).")

    async with bot:
        await charger_les_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
