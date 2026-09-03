import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import json
import os

# =========================================================
#   FICHIER DE STOCKAGE DES WARNS (simple JSON, à remplacer
#   par une vraie DB si besoin plus tard)
# =========================================================
WARNS_FILE = "warns.json"

def load_warns():
    if not os.path.exists(WARNS_FILE):
        return {}
    with open(WARNS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_warns(data):
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class Moderation(commands.Cog):
    """Cog de modération complet : kick, ban, mute, warn, clear, lock, etc."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warns = load_warns()

    # ---------------------------------------------------
    # UTILS
    # ---------------------------------------------------
    def make_embed(self, title, description, color=discord.Color.blurple()):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.timestamp = datetime.datetime.utcnow()
        return embed

    async def cog_check(self, ctx):
        # Vérifie que le bot a les perms de base avant chaque commande du cog
        return True

    # =====================================================
    # KICK
    # =====================================================
    @commands.hybrid_command(name="kick", description="Expulse un membre du serveur")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="Le membre à expulser", reason="Raison de l'expulsion")
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Tu ne peux pas expulser ce membre (rôle supérieur ou égal au tien).")
        if member == ctx.author:
            return await ctx.send("❌ Tu ne peux pas t'expulser toi-même.")

        try:
            await member.send(embed=self.make_embed(
                "Tu as été expulsé",
                f"Serveur : **{ctx.guild.name}**\nRaison : {reason}",
                discord.Color.orange()
            ))
        except discord.Forbidden:
            pass

        await member.kick(reason=f"{reason} | Par {ctx.author}")
        await ctx.send(embed=self.make_embed(
            "👢 Membre expulsé",
            f"**{member}** a été expulsé.\nRaison : {reason}",
            discord.Color.orange()
        ))

    # =====================================================
    # BAN
    # =====================================================
    @commands.hybrid_command(name="ban", description="Bannit un membre du serveur")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(member="Le membre à bannir", reason="Raison du bannissement", delete_days="Jours de messages à supprimer (0-7)")
    async def ban(self, ctx, member: discord.Member, delete_days: int = 0, *, reason: str = "Aucune raison fournie"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Tu ne peux pas bannir ce membre (rôle supérieur ou égal au tien).")

        delete_days = max(0, min(delete_days, 7))

        try:
            await member.send(embed=self.make_embed(
                "Tu as été banni",
                f"Serveur : **{ctx.guild.name}**\nRaison : {reason}",
                discord.Color.red()
            ))
        except discord.Forbidden:
            pass

        await member.ban(reason=f"{reason} | Par {ctx.author}", delete_message_days=delete_days)
        await ctx.send(embed=self.make_embed(
            "🔨 Membre banni",
            f"**{member}** a été banni.\nRaison : {reason}",
            discord.Color.red()
        ))

    # =====================================================
    # UNBAN
    # =====================================================
    @commands.hybrid_command(name="unban", description="Débannit un utilisateur via son ID")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user_id="L'ID de l'utilisateur à débannir")
    async def unban(self, ctx, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user)
            await ctx.send(embed=self.make_embed(
                "✅ Membre débanni",
                f"**{user}** a été débanni.",
                discord.Color.green()
            ))
        except (discord.NotFound, ValueError):
            await ctx.send("❌ Utilisateur introuvable ou ID invalide.")

    # =====================================================
    # TIMEOUT / MUTE (timeout natif Discord)
    # =====================================================
    @commands.hybrid_command(name="mute", description="Met un membre en timeout (mute temporaire)")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Le membre à mute", minutes="Durée en minutes", reason="Raison")
    async def mute(self, ctx, member: discord.Member, minutes: int = 10, *, reason: str = "Aucune raison fournie"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Tu ne peux pas mute ce membre.")

        duration = datetime.timedelta(minutes=minutes)
        try:
            await member.timeout(duration, reason=f"{reason} | Par {ctx.author}")
        except discord.HTTPException:
            return await ctx.send("❌ Impossible d'appliquer le timeout (durée max 28 jours).")

        await ctx.send(embed=self.make_embed(
            "🔇 Membre mute",
            f"**{member}** a été mute pendant **{minutes} min**.\nRaison : {reason}",
            discord.Color.dark_grey()
        ))

    @commands.hybrid_command(name="unmute", description="Retire le timeout d'un membre")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Le membre à unmute")
    async def unmute(self, ctx, member: discord.Member):
        await member.timeout(None)
        await ctx.send(embed=self.make_embed(
            "🔊 Membre unmute",
            f"**{member}** peut de nouveau parler.",
            discord.Color.green()
        ))

    # =====================================================
    # WARN SYSTEM
    # =====================================================
    @commands.hybrid_command(name="warn", description="Avertit un membre")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Le membre à avertir", reason="Raison de l'avertissement")
    async def warn(self, ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        self.warns.setdefault(guild_id, {}).setdefault(user_id, [])
        self.warns[guild_id][user_id].append({
            "reason": reason,
            "moderator": str(ctx.author),
            "date": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        })
        save_warns(self.warns)

        count = len(self.warns[guild_id][user_id])

        try:
            await member.send(embed=self.make_embed(
                "⚠️ Avertissement reçu",
                f"Serveur : **{ctx.guild.name}**\nRaison : {reason}\nTotal d'avertissements : {count}",
                discord.Color.yellow()
            ))
        except discord.Forbidden:
            pass

        await ctx.send(embed=self.make_embed(
            "⚠️ Membre averti",
            f"**{member}** a reçu un avertissement ({count} au total).\nRaison : {reason}",
            discord.Color.yellow()
        ))

    @commands.hybrid_command(name="warnings", description="Affiche les avertissements d'un membre")
    @app_commands.describe(member="Le membre à consulter")
    async def warnings(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        user_warns = self.warns.get(guild_id, {}).get(user_id, [])

        if not user_warns:
            return await ctx.send(f"✅ **{member}** n'a aucun avertissement.")

        embed = self.make_embed(f"⚠️ Avertissements de {member}", f"Total : {len(user_warns)}", discord.Color.yellow())
        for i, w in enumerate(user_warns, start=1):
            embed.add_field(
                name=f"#{i} — {w['date']}",
                value=f"Raison : {w['reason']}\nPar : {w['moderator']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarns", description="Efface tous les avertissements d'un membre")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Le membre concerné")
    async def clearwarns(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in self.warns and user_id in self.warns[guild_id]:
            self.warns[guild_id][user_id] = []
            save_warns(self.warns)

        await ctx.send(embed=self.make_embed(
            "🧹 Avertissements effacés",
            f"Tous les avertissements de **{member}** ont été supprimés.",
            discord.Color.green()
        ))

    # =====================================================
    # CLEAR / PURGE
    # =====================================================
    @commands.hybrid_command(name="clear", description="Supprime un certain nombre de messages")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="Nombre de messages à supprimer (max 100)", member="Filtrer par membre (optionnel)")
    async def clear(self, ctx, amount: int = 10, member: discord.Member = None):
        amount = max(1, min(amount, 100))

        def check(m):
            return member is None or m.author == member

        deleted = await ctx.channel.purge(limit=amount + 1, check=check)  # +1 pour inclure la commande elle-même
        msg = await ctx.send(embed=self.make_embed(
            "🧹 Messages supprimés",
            f"**{len(deleted) - 1}** messages ont été supprimés.",
            discord.Color.green()
        ))
        await asyncio.sleep(3)
        try:
            await msg.delete()
        except discord.NotFound:
            pass

    # =====================================================
    # SLOWMODE
    # =====================================================
    @commands.hybrid_command(name="slowmode", description="Définit le mode lent du salon")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Délai en secondes (0 pour désactiver)")
    async def slowmode(self, ctx, seconds: int):
        seconds = max(0, min(seconds, 21600))  # max discord = 6h
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("✅ Mode lent désactivé.")
        else:
            await ctx.send(f"🐢 Mode lent réglé sur **{seconds}s**.")

    # =====================================================
    # LOCK / UNLOCK
    # =====================================================
    @commands.hybrid_command(name="lock", description="Verrouille le salon (empêche @everyone d'écrire)")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=self.make_embed("🔒 Salon verrouillé", f"{channel.mention} est maintenant verrouillé.", discord.Color.red()))

    @commands.hybrid_command(name="unlock", description="Déverrouille le salon")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=self.make_embed("🔓 Salon déverrouillé", f"{channel.mention} est de nouveau accessible.", discord.Color.green()))

    # =====================================================
    # NICKNAME
    # =====================================================
    @commands.hybrid_command(name="nick", description="Change le pseudo d'un membre")
    @commands.has_permissions(manage_nicknames=True)
    @app_commands.describe(member="Le membre concerné", nickname="Le nouveau pseudo (vide pour reset)")
    async def nick(self, ctx, member: discord.Member, *, nickname: str = None):
        await member.edit(nick=nickname)
        if nickname:
            await ctx.send(f"✅ Pseudo de **{member}** changé en **{nickname}**.")
        else:
            await ctx.send(f"✅ Pseudo de **{member}** réinitialisé.")

    # =====================================================
    # SOFTBAN (ban + unban immédiat pour purger les messages)
    # =====================================================
    @commands.hybrid_command(name="softban", description="Bannit puis débannit immédiatement (purge les messages du membre)")
    @commands.has_permissions(ban_members=True, manage_messages=True)
    @app_commands.describe(member="Le membre à softban", reason="Raison")
    async def softban(self, ctx, member: discord.Member, *, reason: str = "Aucune raison fournie"):
        await member.ban(reason=f"Softban | {reason} | Par {ctx.author}", delete_message_days=1)
        await ctx.guild.unban(member)
        await ctx.send(embed=self.make_embed(
            "🧹 Softban effectué",
            f"**{member}** a été softban (messages purgés, pas banni définitivement).\nRaison : {reason}",
            discord.Color.orange()
        ))

    # =====================================================
    # GESTION DES ERREURS DU COG
    # =====================================================
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.command is None or ctx.command.cog_name != "Moderation":
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour faire ça.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Membre introuvable.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Argument manquant : `{error.param.name}`")
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
