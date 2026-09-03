"""
================================================================
   COG : clear.py
----------------------------------------------------------------
Commande de modération pour nettoyer rapidement un salon en
supprimant un nombre choisi de messages.

Commande : !clear [nombre]
Permission requise : Gérer les messages (Manage Messages)
================================================================
"""

import discord
from discord.ext import commands


class Clear(commands.Cog):
    """Cog regroupant les commandes de nettoyage de salon."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="clear",
        aliases=["purge", "clean"],
        help="Supprime un nombre de messages dans le salon (défaut : 5).",
    )
    @commands.has_permissions(manage_messages=True)      # Réservé aux modérateurs
    @commands.bot_has_permissions(manage_messages=True)  # Vérifie que le bot a bien la permission
    async def clear(self, ctx: commands.Context, nombre: int = 5):
        """
        Supprime `nombre` messages dans le salon actuel (+ le message
        de commande lui-même). Limité à 100 messages par sécurité
        (limite technique de l'API Discord pour la suppression en masse).
        """
        if nombre <= 0:
            await ctx.reply("⚠️ Merci d'indiquer un nombre positif de messages à supprimer.", mention_author=False)
            return

        if nombre > 100:
            await ctx.reply("⚠️ Impossible de supprimer plus de **100 messages** d'un coup (limite Discord).", mention_author=False)
            return

        # +1 pour supprimer aussi le message "!clear X" tapé par le modérateur.
        messages_supprimes = await ctx.channel.purge(limit=nombre + 1)
        nombre_reel = len(messages_supprimes) - 1  # on ne compte pas la commande elle-même

        embed = discord.Embed(
            title="🧹 Salon nettoyé",
            description=f"**{nombre_reel}** message(s) supprimé(s) par {ctx.author.mention}.",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Kōtei 🍥 • Modération")

        # Confirmation auto-détruite après 5 secondes pour ne pas
        # re-polluer le chat qu'on vient de nettoyer.
        confirmation = await ctx.send(embed=embed)
        await confirmation.delete(delay=5)

    @clear.error
    async def clear_error(self, ctx: commands.Context, erreur):
        """Gestion des erreurs propres à la commande !clear."""
        if isinstance(erreur, commands.MissingPermissions):
            await ctx.reply("🚫 Tu n'as pas la permission **Gérer les messages** pour utiliser cette commande.", mention_author=False)
        elif isinstance(erreur, commands.BadArgument):
            await ctx.reply("⚠️ Merci d'indiquer un **nombre** valide. Exemple : `!clear 20`", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Clear(bot))
