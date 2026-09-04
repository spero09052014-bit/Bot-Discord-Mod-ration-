"""
================================================================
   COG : niveaux.py
----------------------------------------------------------------
Système de niveaux (XP) basé sur l'activité dans le chat.

Chaque message envoyé rapporte de l'XP (avec un cooldown pour
éviter le spam-leveling).

Commandes :
  !rank [@membre]  → affiche le niveau/XP d'un membre
  !leaderboard     → classement des membres les plus actifs

Configuration : 100% modifiable avec /config → "Niveaux (XP)",
ou via le .env pour un réglage global de secours :
  - XP_PAR_MESSAGE       → XP gagné par message (défaut : 15)
  - XP_COOLDOWN_SECONDES → délai minimum entre 2 gains d'XP (défaut : 60)
================================================================
"""

import time
import discord
from discord.ext import commands

from . import _xp, _config


class Niveaux(commands.Cog):
    """Cog gérant l'XP, les niveaux et le classement des membres."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Horodatage du dernier gain d'XP par (id_serveur, id_membre), pour le cooldown.
        self.dernier_gain = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        id_serveur = message.guild.id
        xp_cooldown_secondes = _config.obtenir_reglage_int(id_serveur, "XP_COOLDOWN_SECONDES")
        xp_par_message = _config.obtenir_reglage_int(id_serveur, "XP_PAR_MESSAGE")

        cle = (id_serveur, message.author.id)
        maintenant = time.time()

        if maintenant - self.dernier_gain.get(cle, 0) < xp_cooldown_secondes:
            return  # encore en cooldown, pas d'XP cette fois

        self.dernier_gain[cle] = maintenant
        _, nouveau_niveau, a_level_up = _xp.ajouter_xp(id_serveur, message.author.id, xp_par_message)

        if a_level_up:
            try:
                await message.channel.send(f"🎉 GG {message.author.mention}, tu passes **niveau {nouveau_niveau}** !")
            except discord.Forbidden:
                pass

    @commands.hybrid_command(name="rank", aliases=["niveau"], help="Affiche ton niveau et ton XP (ou celui d'un autre membre).")
    @commands.guild_only()
    async def rank(self, ctx: commands.Context, membre: discord.Member = None):
        membre = membre or ctx.author
        xp_total = _xp.obtenir_xp(ctx.guild.id, membre.id)
        niveau_actuel = _xp.niveau_depuis_xp(xp_total)

        xp_deja_utilisee = sum(_xp.xp_necessaire_pour(n) for n in range(niveau_actuel))
        xp_dans_le_niveau = xp_total - xp_deja_utilisee
        xp_requise_niveau = _xp.xp_necessaire_pour(niveau_actuel)

        embed = discord.Embed(title=f"📈 Niveau de {membre.display_name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="Niveau", value=str(niveau_actuel), inline=True)
        embed.add_field(name="XP total", value=str(xp_total), inline=True)
        embed.add_field(name="Progression", value=f"{xp_dans_le_niveau} / {xp_requise_niveau} XP", inline=True)
        embed.set_footer(text="Kōtei 🍥")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="leaderboard", aliases=["classement", "top"], help="Affiche le classement des membres les plus actifs.")
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context):
        top = _xp.classement(ctx.guild.id, limite=10)

        if not top:
            await ctx.reply("📉 Personne n'a encore gagné d'XP sur ce serveur.", mention_author=False)
            return

        medailles = ["🥇", "🥈", "🥉"]
        lignes = []
        for index, (id_membre, xp_total) in enumerate(top):
            medaille = medailles[index] if index < 3 else f"`#{index + 1}`"
            niveau = _xp.niveau_depuis_xp(xp_total)
            lignes.append(f"{medaille} <@{id_membre}> — Niveau {niveau} ({xp_total} XP)")

        embed = discord.Embed(
            title=f"🏆 Classement — {ctx.guild.name}",
            description="\n".join(lignes),
            color=discord.Color.gold(),
        )
        embed.set_footer(text="Kōtei 🍥")
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Niveaux(bot))
