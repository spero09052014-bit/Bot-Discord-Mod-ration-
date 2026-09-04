"""
================================================================
   COG : staffcheck.py
----------------------------------------------------------------
Commande sensible réservée aux FONDATEURS du serveur. Elle scanne
les 100 dernières entrées des bûches d'audit (Audit Logs) de
Discord pour compter le nombre de bans et de kicks effectués par
un modérateur donné.

Objectif : détecter un éventuel abus de pouvoir (un modérateur
qui bannirait/exclurait anormalement beaucoup de membres).

Commande : !staffcheck @membre
Accès : uniquement les fondateurs — 100% configurable avec
/config → "Modération" (sélectionne les membres dans le menu),
ou via FOUNDER_IDS dans le .env pour un réglage global de secours.
================================================================
"""

import discord
from discord.ext import commands

from . import _config

# Seuil au-delà duquel on considère l'activité comme suspecte.
# Ajuste cette valeur selon la taille et l'activité de ton serveur.
SEUIL_ALERTE = 10


def est_fondateur():
    """
    Décorateur de vérification personnalisé : autorise la commande
    uniquement si l'auteur du message fait partie des fondateurs
    configurés pour ce serveur.
    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            return False
        return ctx.author.id in _config.obtenir_founder_ids(ctx.guild.id)
    return commands.check(predicate)


class StaffCheck(commands.Cog):
    """Cog dédié à l'audit interne des actions de modération."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="staffcheck",
        help="[Fondateurs uniquement] Analyse les actions de modération d'un membre.",
    )
    @est_fondateur()
    @commands.guild_only()
    @commands.bot_has_permissions(view_audit_log=True)  # Le bot doit pouvoir lire l'Audit Log
    async def staffcheck(self, ctx: commands.Context, membre: discord.Member):
        """
        Parcourt les 100 dernières entrées de l'Audit Log du serveur
        et compte combien de bans / kicks ont été effectués par `membre`.
        """
        async with ctx.typing():
            nombre_bans = 0
            nombre_kicks = 0
            dernieres_actions = []  # petit historique lisible pour l'embed

            # discord.py permet de parcourir l'Audit Log de façon asynchrone.
            async for entree in ctx.guild.audit_logs(limit=100):
                # On ne s'intéresse qu'aux actions faites PAR le membre analysé.
                if entree.user is None or entree.user.id != membre.id:
                    continue

                if entree.action == discord.AuditLogAction.ban:
                    nombre_bans += 1
                    dernieres_actions.append(f"🔨 Ban → {entree.target} ({entree.created_at:%d/%m %H:%M})")

                elif entree.action == discord.AuditLogAction.kick:
                    nombre_kicks += 1
                    dernieres_actions.append(f"👢 Kick → {entree.target} ({entree.created_at:%d/%m %H:%M})")

            total_actions = nombre_bans + nombre_kicks

            if total_actions >= SEUIL_ALERTE:
                couleur = discord.Color.red()
                verdict = "🚨 **Activité suspecte détectée !**"
            elif total_actions > 0:
                couleur = discord.Color.orange()
                verdict = "🟠 Activité de modération normale."
            else:
                couleur = discord.Color.green()
                verdict = "✅ Aucune action de modération récente."

            embed = discord.Embed(
                title=f"🕵️ Rapport d'audit — {membre.display_name}",
                description=verdict,
                color=couleur,
            )
            embed.add_field(name="Bans effectués", value=str(nombre_bans), inline=True)
            embed.add_field(name="Kicks effectués", value=str(nombre_kicks), inline=True)
            embed.add_field(name="Total (100 dernières entrées)", value=str(total_actions), inline=True)

            if dernieres_actions:
                # Limité aux 10 dernières actions pour respecter la limite
                # de caractères d'un champ d'embed Discord.
                historique = "\n".join(dernieres_actions[:10])
                embed.add_field(name="Détail des dernières actions", value=historique, inline=False)

            embed.set_thumbnail(url=membre.display_avatar.url)
            embed.set_footer(text=f"Analyse demandée par {ctx.author.display_name} • Kōtei 🍥")

        await ctx.reply(embed=embed, mention_author=False)

    @staffcheck.error
    async def staffcheck_error(self, ctx: commands.Context, erreur):
        """Gestion des erreurs propres à la commande !staffcheck."""
        if isinstance(erreur, commands.CheckFailure):
            await ctx.reply("🚫 Cette commande est réservée aux **fondateurs** du serveur.", mention_author=False)
        elif isinstance(erreur, commands.MemberNotFound):
            await ctx.reply("⚠️ Membre introuvable. Utilise une mention valide : `!staffcheck @membre`", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffCheck(bot))
