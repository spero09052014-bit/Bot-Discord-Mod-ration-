import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import aiohttp

CONFIG_FILE = "bot_config.json"

DEFAULT_CONFIG = {
    "embed_color": "#5865F2",   # couleur par défaut des embeds (Blurple)
    "status": "online",         # online / idle / dnd / invisible
    "activity_type": "playing", # playing / watching / listening / competing / streaming
    "activity_text": "veiller au grain 👀"
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        # complète les clés manquantes si le fichier existe déjà mais est incomplet
        for k, v in DEFAULT_CONFIG.items():
            data.setdefault(k, v)
        return data


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


ACTIVITY_MAP = {
    "playing": discord.ActivityType.playing,
    "watching": discord.ActivityType.watching,
    "listening": discord.ActivityType.listening,
    "competing": discord.ActivityType.competing,
}

STATUS_MAP = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible,
}


class BotConfig(commands.Cog):
    """Cog permettant de personnaliser l'apparence et la présence du bot (owner uniquement)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_config()

    async def cog_load(self):
        # Applique la config sauvegardée dès que le cog est chargé
        await self.apply_presence()

    async def apply_presence(self):
        activity_type = ACTIVITY_MAP.get(self.config["activity_type"], discord.ActivityType.playing)
        activity = discord.Activity(type=activity_type, name=self.config["activity_text"])
        status = STATUS_MAP.get(self.config["status"], discord.Status.online)
        await self.bot.change_presence(status=status, activity=activity)

    def get_embed_color(self) -> discord.Color:
        try:
            return discord.Color(int(self.config["embed_color"].lstrip("#"), 16))
        except (ValueError, AttributeError):
            return discord.Color.blurple()

    # =====================================================
    # PSEUDO DU BOT (sur le serveur)
    # =====================================================
    @commands.hybrid_command(name="botnick", description="Change le pseudo du bot sur ce serveur")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(nickname="Le nouveau pseudo du bot (vide pour reset)")
    async def botnick(self, ctx, *, nickname: str = None):
        await ctx.guild.me.edit(nick=nickname)
        if nickname:
            await ctx.send(f"✅ Mon pseudo sur ce serveur est maintenant **{nickname}**.")
        else:
            await ctx.send("✅ Mon pseudo a été réinitialisé.")

    # =====================================================
    # AVATAR DU BOT (global, nécessite l'owner de l'application)
    # =====================================================
    @commands.hybrid_command(name="botavatar", description="Change l'avatar global du bot (admin uniquement)")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(url="Lien direct vers l'image (png/jpg)")
    async def botavatar(self, ctx, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send("❌ Impossible de télécharger cette image.")
                image_bytes = await resp.read()

        try:
            await self.bot.user.edit(avatar=image_bytes)
        except discord.HTTPException as e:
            return await ctx.send(f"❌ Erreur lors du changement d'avatar : {e}")

        await ctx.send("✅ Avatar du bot mis à jour !")

    # =====================================================
    # BANNIÈRE DU BOT (global, owner uniquement)
    # =====================================================
    @commands.hybrid_command(name="botbanner", description="Change la bannière globale du bot (admin uniquement)")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(url="Lien direct vers l'image (png/jpg)")
    async def botbanner(self, ctx, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send("❌ Impossible de télécharger cette image.")
                image_bytes = await resp.read()

        try:
            await self.bot.user.edit(banner=image_bytes)
        except discord.HTTPException as e:
            return await ctx.send(f"❌ Erreur lors du changement de bannière : {e}")

        await ctx.send("✅ Bannière du bot mise à jour !")

    # =====================================================
    # STATUT (en ligne / absent / ne pas déranger / invisible)
    # =====================================================
    @commands.hybrid_command(name="botstatus", description="Change le statut du bot")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(status="online, idle, dnd ou invisible")
    @app_commands.choices(status=[
        app_commands.Choice(name="En ligne", value="online"),
        app_commands.Choice(name="Absent", value="idle"),
        app_commands.Choice(name="Ne pas déranger", value="dnd"),
        app_commands.Choice(name="Invisible", value="invisible"),
    ])
    async def botstatus(self, ctx, status: str):
        if status not in STATUS_MAP:
            return await ctx.send("❌ Statut invalide. Choix possibles : online, idle, dnd, invisible.")

        self.config["status"] = status
        save_config(self.config)
        await self.apply_presence()
        await ctx.send(f"✅ Statut changé en **{status}**.")

    # =====================================================
    # ACTIVITÉ ("Joue à...", "Regarde...", etc.)
    # =====================================================
    @commands.hybrid_command(name="botactivity", description="Change l'activité affichée par le bot")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(type="Type d'activité", text="Texte affiché")
    @app_commands.choices(type=[
        app_commands.Choice(name="Joue à", value="playing"),
        app_commands.Choice(name="Regarde", value="watching"),
        app_commands.Choice(name="Écoute", value="listening"),
        app_commands.Choice(name="Participe à", value="competing"),
    ])
    async def botactivity(self, ctx, type: str, *, text: str):
        if type not in ACTIVITY_MAP:
            return await ctx.send("❌ Type invalide. Choix possibles : playing, watching, listening, competing.")

        self.config["activity_type"] = type
        self.config["activity_text"] = text
        save_config(self.config)
        await self.apply_presence()
        await ctx.send(f"✅ Activité mise à jour : **{type} {text}**.")

    # =====================================================
    # COULEUR DES EMBEDS DU BOT
    # =====================================================
    @commands.hybrid_command(name="botcolor", description="Change la couleur utilisée dans les embeds du bot")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(hex_color="Couleur au format hexadécimal, ex: #FF0000")
    async def botcolor(self, ctx, hex_color: str):
        hex_color = hex_color.strip()
        try:
            int(hex_color.lstrip("#"), 16)
        except ValueError:
            return await ctx.send("❌ Couleur invalide. Utilise un format hexadécimal, ex : `#FF0000`.")

        self.config["embed_color"] = hex_color
        save_config(self.config)

        embed = discord.Embed(
            title="🎨 Couleur mise à jour",
            description=f"Les embeds du bot utiliseront désormais cette couleur.",
            color=self.get_embed_color()
        )
        await ctx.send(embed=embed)

    # =====================================================
    # RÉCAPITULATIF DE LA CONFIG ACTUELLE
    # =====================================================
    @commands.hybrid_command(name="botconfig", description="Affiche la configuration actuelle de l'apparence du bot")
    async def botconfig(self, ctx):
        embed = discord.Embed(
            title=f"⚙️ Configuration de {self.bot.user.name}",
            color=self.get_embed_color()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Statut", value=self.config["status"], inline=True)
        embed.add_field(name="Activité", value=f"{self.config['activity_type']} {self.config['activity_text']}", inline=True)
        embed.add_field(name="Couleur embeds", value=self.config["embed_color"], inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BotConfig(bot))
