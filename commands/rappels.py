"""
================================================================
   COG : rappels.py
----------------------------------------------------------------
Rappels personnels programmés.

Commande : !remind <durée> <message>
Exemple  : !remind 10m Boire de l'eau

⚠️ Les rappels sont stockés EN MÉMOIRE uniquement : si le bot
   redémarre avant l'échéance, le rappel est perdu. Très bien pour
   des rappels courts (minutes/heures) ; à éviter pour des rappels
   à plusieurs jours sur un hébergement gratuit qui peut redémarrer
   (comme Render en offre gratuite).
================================================================
"""

import asyncio
import discord
from discord.ext import commands

from . import _utils


class Rappels(commands.Cog):
    """Cog gérant les rappels personnels programmés."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="remind", aliases=["rappel"], help="Programme un rappel. Ex : !remind 10m Boire de l'eau")
    async def remind(self, ctx: commands.Context, duree: str, *, message: str):
        delta = _utils.parser_duree(duree)
        if delta is None:
            await ctx.reply("⚠️ Format de durée invalide. Utilise par exemple : `10m`, `2h`, `1j`.", mention_author=False)
            return

        await ctx.reply(
            f"⏰ D'accord {ctx.author.mention}, je te rappellerai **{message}** dans {duree}.",
            mention_author=False,
        )

        await asyncio.sleep(delta.total_seconds())

        try:
            await ctx.channel.send(f"⏰ {ctx.author.mention}, rappel : **{message}**")
        except discord.Forbidden:
            pass

    @remind.error
    async def remind_error(self, ctx: commands.Context, erreur):
        if isinstance(erreur, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Syntaxe : `!remind <durée> <message>`. Exemple : `!remind 30m Pause café`", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Rappels(bot))
