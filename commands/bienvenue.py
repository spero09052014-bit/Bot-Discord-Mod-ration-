"""
================================================================
   COG : bienvenue.py
----------------------------------------------------------------
Message de bienvenue automatique + attribution d'un rôle par
défaut aux nouveaux membres. Message d'au revoir en bonus quand
quelqu'un quitte le serveur.

Configuration (100% modifiable avec /config → "Bienvenue", ou
via le .env pour un réglage global de secours) :
  - WELCOME_CHANNEL_ID → salon où poster bienvenue/au revoir (vide = désactivé)
  - AUTOROLE_ID        → ID du rôle donné automatiquement (vide = désactivé)
================================================================
"""

import discord
from discord.ext import commands

from . import _config


class Bienvenue(commands.Cog):
    """Cog gérant l'accueil des nouveaux membres."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, membre: discord.Member):
        id_serveur = membre.guild.id

        # --- Attribution automatique du rôle ---
        autorole_id = _config.obtenir_reglage(id_serveur, "AUTOROLE_ID")
        if autorole_id.isdigit():
            role = membre.guild.get_role(int(autorole_id))
            if role:
                try:
                    await membre.add_roles(role, reason="Rôle automatique à l'arrivée")
                except discord.Forbidden:
                    pass

        # --- Message de bienvenue ---
        welcome_channel_id = _config.obtenir_reglage(id_serveur, "WELCOME_CHANNEL_ID")
        if not welcome_channel_id.isdigit():
            return

        salon = membre.guild.get_channel(int(welcome_channel_id))
        if salon is None:
            return

        embed = discord.Embed(
            title="🍥 Nouveau membre !",
            description=f"Bienvenue sur **{membre.guild.name}**, {membre.mention} !",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.set_footer(text=f"Membre n°{membre.guild.member_count} • Kōtei 🍥")

        try:
            await salon.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, membre: discord.Member):
        welcome_channel_id = _config.obtenir_reglage(membre.guild.id, "WELCOME_CHANNEL_ID")
        if not welcome_channel_id.isdigit():
            return

        salon = membre.guild.get_channel(int(welcome_channel_id))
        if salon is None:
            return

        embed = discord.Embed(
            description=f"👋 **{membre.display_name}** a quitté le serveur.",
            color=discord.Color.dark_grey(),
        )
        try:
            await salon.send(embed=embed)
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Bienvenue(bot))
