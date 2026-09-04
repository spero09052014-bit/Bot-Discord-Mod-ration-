"""
================================================================
   COG : sondages.py
----------------------------------------------------------------
Crée des sondages rapides avec réactions.

  !poll <question>                          → sondage Oui/Non (👍/👎)
  !poll <question> ; option1 ; option2 ...  → sondage à choix multiples (jusqu'à 10)

Les options se séparent avec un point-virgule (;).
Exemple : !poll Quel jeu ce soir ? ; Minecraft ; Valorant ; Autre
================================================================
"""

import discord
from discord.ext import commands

EMOJIS_NUMEROS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


class Sondages(commands.Cog):
    """Cog permettant de créer des sondages rapides à réactions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="poll",
        aliases=["sondage"],
        help="Crée un sondage. Ex : !poll Question ; Option1 ; Option2",
    )
    @commands.guild_only()
    async def poll(self, ctx: commands.Context, *, contenu: str):
        morceaux = [partie.strip() for partie in contenu.split(";") if partie.strip()]
        question = morceaux[0]
        options = morceaux[1:]

        if len(options) > 10:
            await ctx.reply("⚠️ Maximum 10 options par sondage.", mention_author=False)
            return

        embed = discord.Embed(title="📊 Sondage", description=f"**{question}**", color=discord.Color.purple())
        embed.set_footer(text=f"Sondage lancé par {ctx.author.display_name} • Kōtei 🍥")

        if not options:
            # Pas d'options précisées : sondage simple Oui/Non.
            embed.add_field(name="\u200b", value="👍 Oui   /   👎 Non", inline=False)
            message_sondage = await ctx.send(embed=embed)
            await message_sondage.add_reaction("👍")
            await message_sondage.add_reaction("👎")
        else:
            lignes = [f"{EMOJIS_NUMEROS[i]} {option}" for i, option in enumerate(options)]
            embed.add_field(name="Options", value="\n".join(lignes), inline=False)
            message_sondage = await ctx.send(embed=embed)
            for i in range(len(options)):
                await message_sondage.add_reaction(EMOJIS_NUMEROS[i])

    @poll.error
    async def poll_error(self, ctx: commands.Context, erreur):
        if isinstance(erreur, commands.MissingRequiredArgument):
            await ctx.reply("⚠️ Merci d'indiquer une question. Exemple : `!poll Minecraft ou Valorant ce soir ?`", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sondages(bot))
