"""
================================================================
   COG : warn.py
----------------------------------------------------------------
Système d'avertissements persistant (stocké dans data/warns.json).

Commandes :
  !warn @membre [raison]     → ajoute un avertissement
  !warnings @membre          → liste les avertissements d'un membre
  !unwarn @membre [index]    → retire un avertissement précis

Permission requise : Gérer les messages (Manage Messages)
================================================================
"""

import datetime
import discord
from discord.ext import commands

from . import _stockage
from . import _modlog


class Warn(commands.Cog):
    """Cog regroupant le système d'avertissements des membres."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="warn", help="Ajoute un avertissement à un membre.")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, membre: discord.Member, *, raison: str = "Aucune raison précisée"):
        """Ajoute un avertissement persistant à `membre` et prévient tout le monde."""
        date_iso = datetime.datetime.utcnow().isoformat()
        total_warns = _stockage.ajouter_warn(ctx.guild.id, membre.id, raison, ctx.author.id, date_iso)

        embed = discord.Embed(
            title="⚠️ Avertissement ajouté",
            description=f"{membre.mention} a été averti par {ctx.author.mention}.",
            color=discord.Color.yellow(),
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="Total d'avertissements", value=str(total_warns), inline=True)
        embed.set_footer(text="Kōtei 🍥 • Modération")
        await ctx.reply(embed=embed, mention_author=False)

        # On prévient le membre en message privé, sans bloquer si ses DM sont fermés.
        try:
            await membre.send(
                f"⚠️ Tu as reçu un avertissement sur **{ctx.guild.name}**.\n"
                f"Raison : {raison}\n"
                f"Total d'avertissements : {total_warns}"
            )
        except discord.Forbidden:
            pass

        await _modlog.envoyer_log(
            self.bot,
            id_serveur=ctx.guild.id,
            titre="⚠️ Avertissement",
            description=f"{membre.mention} averti par {ctx.author.mention}",
            couleur=discord.Color.yellow(),
            champs={"Raison": raison, "Total": total_warns},
        )

    @commands.hybrid_command(name="warnings", aliases=["warnlist"], help="Liste les avertissements d'un membre.")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def warnings(self, ctx: commands.Context, membre: discord.Member):
        """Affiche la liste complète des avertissements actifs d'un membre."""
        warns = _stockage.lister_warns(ctx.guild.id, membre.id)

        if not warns:
            await ctx.reply(f"✅ {membre.mention} n'a aucun avertissement.", mention_author=False)
            return

        embed = discord.Embed(
            title=f"📋 Avertissements de {membre.display_name}",
            color=discord.Color.yellow(),
        )
        for index, warn_data in enumerate(warns):
            date_lisible = warn_data["date"].split("T")[0]
            embed.add_field(
                name=f"#{index} — {date_lisible}",
                value=f"Raison : {warn_data['raison']}\nPar : <@{warn_data['moderateur']}>",
                inline=False,
            )
        embed.set_footer(text=f"{len(warns)} avertissement(s) au total • Kōtei 🍥")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="unwarn", help="Retire un avertissement précis d'un membre (voir !warnings pour l'index).")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def unwarn(self, ctx: commands.Context, membre: discord.Member, index: int):
        """Retire l'avertissement numéro `index` (visible via !warnings)."""
        succes = _stockage.retirer_warn(ctx.guild.id, membre.id, index)

        if succes:
            await ctx.reply(f"✅ Avertissement #{index} retiré pour {membre.mention}.", mention_author=False)
            await _modlog.envoyer_log(
                self.bot,
                id_serveur=ctx.guild.id,
                titre="✅ Avertissement retiré",
                description=f"Avertissement #{index} de {membre.mention} retiré par {ctx.author.mention}",
                couleur=discord.Color.green(),
            )
        else:
            await ctx.reply(f"⚠️ Aucun avertissement à l'index #{index} pour ce membre. Utilise `!warnings @membre` pour voir les index valides.", mention_author=False)

    @warn.error
    @warnings.error
    @unwarn.error
    async def erreurs_warn(self, ctx: commands.Context, erreur):
        """Gestion mutualisée des erreurs pour toutes les commandes de ce Cog."""
        if isinstance(erreur, commands.MissingPermissions):
            await ctx.reply("🚫 Tu n'as pas la permission **Gérer les messages** pour utiliser cette commande.", mention_author=False)
        elif isinstance(erreur, commands.MemberNotFound):
            await ctx.reply("⚠️ Membre introuvable. Exemple : `!warn @membre Spam répété`", mention_author=False)
        elif isinstance(erreur, commands.BadArgument):
            await ctx.reply("⚠️ Argument invalide. Vérifie la syntaxe de la commande.", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Warn(bot))
