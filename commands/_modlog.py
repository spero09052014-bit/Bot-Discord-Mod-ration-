"""
================================================================
   JOURNAL DE MODÉRATION — _modlog.py
----------------------------------------------------------------
⚠️ Ce fichier commence par "_" : bot.py l'ignore lors du
   chargement automatique des Cogs. Il expose une seule fonction,
   utilisée par tous les Cogs de modération (warn, sanctions,
   antispam...) pour envoyer un embed récapitulatif dans le
   salon défini par MODLOG_CHANNEL_ID (.env).

Si MODLOG_CHANNEL_ID n'est pas configuré, la fonction ne fait
rien silencieusement : le bot fonctionne normalement, seul le
journal centralisé est désactivé.
================================================================
"""

import os
import discord

MODLOG_CHANNEL_ID = os.getenv("MODLOG_CHANNEL_ID", "")


async def envoyer_log(bot, titre: str, description: str, couleur=discord.Color.orange(), champs: dict | None = None):
    """
    Envoie un embed de log dans le salon MODLOG_CHANNEL_ID.

    - bot : l'instance du bot (pour retrouver le salon via son cache)
    - titre / description : contenu principal de l'embed
    - couleur : discord.Color (rouge pour un ban, orange pour un warn, etc.)
    - champs : dict optionnel {nom_du_champ: valeur} ajouté à l'embed
    """
    if not MODLOG_CHANNEL_ID.isdigit():
        return  # pas configuré : on ignore silencieusement

    salon = bot.get_channel(int(MODLOG_CHANNEL_ID))
    if salon is None:
        return  # salon introuvable (mauvais ID, ou bot pas encore prêt)

    embed = discord.Embed(title=titre, description=description, color=couleur)
    if champs:
        for nom, valeur in champs.items():
            embed.add_field(name=nom, value=str(valeur), inline=True)
    embed.set_footer(text="Kōtei 🍥 • Journal de modération")

    try:
        await salon.send(embed=embed)
    except discord.Forbidden:
        # Le bot n'a pas la permission d'écrire dans ce salon : on ignore
        # plutôt que de faire planter la commande de modération d'origine.
        pass
