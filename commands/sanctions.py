"""
================================================================
   COG : sanctions.py
----------------------------------------------------------------
Commandes de modération "lourdes" : mute (timeout), kick, ban.
Chaque sanction :
  1. Prévient le membre en message privé (si possible)
  2. Applique la sanction
  3. Confirme dans le salon
  4. Journalise l'action dans le salon MODLOG_CHANNEL_ID (.env)

Commandes :
  !mute @membre <durée> [raison]   → ex: !mute @Toto 10m Spam
  !unmute @membre [raison]
  !kick @membre [raison]
  !ban @membre [raison]
  !unban <id_utilisateur> [raison]

Permissions requises : respectivement Modérer les membres,
Expulser des membres, Bannir des membres (permissions Discord
natives — configurables sur le rôle Staff dans les paramètres
du serveur, aucune config supplémentaire côté bot).
================================================================
"""

import discord
from discord.ext import commands

from . import _utils
from . import _modlog


class Sanctions(commands.Cog):
    """Cog regroupant les sanctions de modération (mute/kick/ban)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # !mute — timeout temporaire
    # ------------------------------------------------------------------
    @commands.command(name="mute", help="Rend muet un membre pendant une durée donnée. Ex : !mute @membre 10m Spam")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.guild_only()
    async def mute(self, ctx: commands.Context, membre: discord.Member, duree: str, *, raison: str = "Aucune raison précisée"):
        delta = _utils.parser_duree(duree)
        if delta is None:
            await ctx.reply(
                "⚠️ Format de durée invalide. Utilise par exemple : `10m` (minutes), `2h` (heures), `1j` (jour), `1w` (semaine).",
                mention_author=False,
            )
            return

        await membre.timeout(delta, reason=f"{raison} (par {ctx.author})")

        embed = discord.Embed(
            title="🔇 Membre mis en sourdine",
            description=f"{membre.mention} a été rendu muet pendant **{duree}** par {ctx.author.mention}.",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

        try:
            await membre.send(f"🔇 Tu as été rendu muet sur **{ctx.guild.name}** pendant {duree}.\nRaison : {raison}")
        except discord.Forbidden:
            pass

        await _modlog.envoyer_log(
            self.bot, titre="🔇 Mute", description=f"{membre.mention} muté par {ctx.author.mention}",
            couleur=discord.Color.orange(), champs={"Durée": duree, "Raison": raison},
        )

    # ------------------------------------------------------------------
    # !unmute — retire le timeout
    # ------------------------------------------------------------------
    @commands.command(name="unmute", help="Retire la sourdine d'un membre.")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.guild_only()
    async def unmute(self, ctx: commands.Context, membre: discord.Member, *, raison: str = "Aucune raison précisée"):
        await membre.timeout(None, reason=f"{raison} (par {ctx.author})")

        await ctx.reply(f"🔊 {membre.mention} peut de nouveau parler.", mention_author=False)
        await _modlog.envoyer_log(
            self.bot, titre="🔊 Unmute", description=f"{membre.mention} démuté par {ctx.author.mention}",
            couleur=discord.Color.green(), champs={"Raison": raison},
        )

    # ------------------------------------------------------------------
    # !kick
    # ------------------------------------------------------------------
    @commands.command(name="kick", help="Expulse un membre du serveur.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx: commands.Context, membre: discord.Member, *, raison: str = "Aucune raison précisée"):
        try:
            await membre.send(f"👢 Tu as été expulsé de **{ctx.guild.name}**.\nRaison : {raison}")
        except discord.Forbidden:
            pass

        await membre.kick(reason=f"{raison} (par {ctx.author})")

        embed = discord.Embed(
            title="👢 Membre expulsé",
            description=f"{membre.mention} a été expulsé par {ctx.author.mention}.",
            color=discord.Color.red(),
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

        await _modlog.envoyer_log(
            self.bot, titre="👢 Kick", description=f"{membre} expulsé par {ctx.author.mention}",
            couleur=discord.Color.red(), champs={"Raison": raison},
        )

    # ------------------------------------------------------------------
    # !ban
    # ------------------------------------------------------------------
    @commands.command(name="ban", help="Bannit un membre du serveur.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx: commands.Context, membre: discord.Member, *, raison: str = "Aucune raison précisée"):
        try:
            await membre.send(f"🔨 Tu as été banni de **{ctx.guild.name}**.\nRaison : {raison}")
        except discord.Forbidden:
            pass

        await membre.ban(reason=f"{raison} (par {ctx.author})", delete_message_seconds=0)

        embed = discord.Embed(
            title="🔨 Membre banni",
            description=f"{membre.mention} a été banni par {ctx.author.mention}.",
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

        await _modlog.envoyer_log(
            self.bot, titre="🔨 Ban", description=f"{membre} banni par {ctx.author.mention}",
            couleur=discord.Color.dark_red(), champs={"Raison": raison},
        )

    # ------------------------------------------------------------------
    # !unban — nécessite l'ID (le membre n'est plus sur le serveur)
    # ------------------------------------------------------------------
    @commands.command(name="unban", help="Débannit un utilisateur via son ID Discord.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx: commands.Context, id_utilisateur: int, *, raison: str = "Aucune raison précisée"):
        try:
            await ctx.guild.unban(discord.Object(id=id_utilisateur), reason=f"{raison} (par {ctx.author})")
        except discord.NotFound:
            await ctx.reply("⚠️ Aucun bannissement trouvé pour cet ID.", mention_author=False)
            return

        await ctx.reply(f"✅ Utilisateur `{id_utilisateur}` débanni par {ctx.author.mention}.", mention_author=False)
        await _modlog.envoyer_log(
            self.bot, titre="✅ Unban", description=f"Utilisateur `{id_utilisateur}` débanni par {ctx.author.mention}",
            couleur=discord.Color.green(), champs={"Raison": raison},
        )

    # ------------------------------------------------------------------
    # Gestion mutualisée des erreurs pour toutes les commandes du Cog
    # ------------------------------------------------------------------
    @mute.error
    @unmute.error
    @kick.error
    @ban.error
    @unban.error
    async def erreurs_sanctions(self, ctx: commands.Context, erreur):
        if isinstance(erreur, commands.MissingPermissions):
            await ctx.reply(f"🚫 Il te manque une permission Discord pour utiliser cette commande (`{erreur.missing_permissions}`).", mention_author=False)
        elif isinstance(erreur, commands.BotMissingPermissions):
            await ctx.reply(f"⚠️ Le bot n'a pas la permission nécessaire pour effectuer cette action (`{erreur.missing_permissions}`).", mention_author=False)
        elif isinstance(erreur, commands.MemberNotFound):
            await ctx.reply("⚠️ Membre introuvable. Utilise une mention valide, ex : `!kick @membre Raison`", mention_author=False)
        elif isinstance(erreur, discord.Forbidden):
            await ctx.reply("🚫 Le bot n'a pas un rôle suffisamment élevé dans la hiérarchie pour sanctionner ce membre.", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sanctions(bot))
