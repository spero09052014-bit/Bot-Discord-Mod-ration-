"""
================================================================
   COG : suggestions.py
----------------------------------------------------------------
Boîte à suggestions : les membres proposent une idée via une
commande, elle est postée dans un salon dédié avec des réactions
👍/👎 pour que la communauté vote dessus.

Commande : !suggest <texte de la suggestion>
Configuration : 100% modifiable avec /config → "Suggestions"
(sélectionne simplement le salon dans le menu), ou via
SUGGESTIONS_CHANNEL_ID dans le .env pour un réglage global de secours.
================================================================
"""

import discord
from discord.ext import commands

from . import _config


class Suggestions(commands.Cog):
    """Cog gérant la boîte à suggestions de la communauté."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="suggest", aliases=["suggestion"], help="Propose une suggestion à la communauté.")
    @commands.guild_only()
    async def suggest(self, ctx: commands.Context, *, texte: str):
        suggestions_channel_id = _config.obtenir_reglage(ctx.guild.id, "SUGGESTIONS_CHANNEL_ID")
        if not suggestions_channel_id.isdigit():
            await ctx.reply("⚠️ La boîte à suggestions n'est pas configurée. Un administrateur peut la régler avec `/config` → \"Suggestions\".", mention_author=False)
            return

        salon = ctx.guild.get_channel(int(suggestions_channel_id))
        if salon is None:
            await ctx.reply("⚠️ Le salon de suggestions configuré est introuvable.", mention_author=False)
            return

        embed = discord.Embed(
            title="💡 Nouvelle suggestion",
            description=texte,
            color=discord.Color.blue(),
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="Vote avec 👍 ou 👎 • Kōtei 🍥")

        message_suggestion = await salon.send(embed=embed)
        await message_suggestion.add_reaction("👍")
        await message_suggestion.add_reaction("👎")

        await ctx.reply(f"✅ Ta suggestion a été postée dans {salon.mention} !", mention_author=False)

    @suggest.error
    async def suggest_error(self, ctx: commands.Context, erreur):
        if isinstance(erreur, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Merci d'écrire ta suggestion. Exemple : `!suggest Ajouter un salon musique`", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Suggestions(bot))
