"""
================================================================
   COG : ping.py
----------------------------------------------------------------
Commande simple pour vérifier que le bot est en ligne et
mesurer sa latence (temps de réponse avec les serveurs Discord).

Commande : !ping
================================================================
"""

import discord
from discord.ext import commands


class Ping(commands.Cog):
    """Cog regroupant les commandes liées au diagnostic du bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", help="Affiche la latence actuelle du bot.")
    async def ping(self, ctx: commands.Context):
        """Calcule la latence websocket du bot et l'affiche dans un embed."""
        latence_ms = round(self.bot.latency * 1000)

        # On choisit une couleur/texte selon la qualité de la latence.
        if latence_ms < 150:
            couleur = discord.Color.green()
            statut = "Excellente 🟢"
        elif latence_ms < 300:
            couleur = discord.Color.orange()
            statut = "Correcte 🟠"
        else:
            couleur = discord.Color.red()
            statut = "Élevée 🔴"

        embed = discord.Embed(
            title="🏓 Pong !",
            description=f"Latence actuelle du bot **{self.bot.user.name}**.",
            color=couleur,
        )
        embed.add_field(name="Latence", value=f"`{latence_ms} ms`", inline=True)
        embed.add_field(name="Statut", value=statut, inline=True)
        embed.set_footer(text="Kōtei 🍥")

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    """
    Fonction OBLIGATOIRE appelée automatiquement par bot.py
    (via load_extension) pour enregistrer ce Cog auprès du bot.
    """
    await bot.add_cog(Ping(bot))
