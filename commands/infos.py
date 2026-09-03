"""
================================================================
   COG : infos.py
----------------------------------------------------------------
Regroupe deux commandes d'information :

  • !serverstats → Statistiques générales du serveur.
  • !resume      → [Staff uniquement] Lit les 50 derniers messages
                    du salon et génère un résumé automatique via
                    l'API Anthropic (Claude).

Configuration requise dans le .env :
  - STAFF_ROLE_NAME=Staff        (nom exact du rôle staff)
  - ANTHROPIC_API_KEY=sk-ant-... (clé API Claude, pour !resume)
    Sans clé, !resume fonctionne quand même en mode "simplifié".
================================================================
"""

import os
import discord
from discord.ext import commands

# La librairie "anthropic" est optionnelle : si elle n'est pas installée
# ou que la clé API est absente, !resume basculera automatiquement sur
# un résumé "simple" (statistique) plutôt que de planter.
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_DISPONIBLE = True
except ImportError:
    ANTHROPIC_DISPONIBLE = False

STAFF_ROLE_NAME = os.getenv("STAFF_ROLE_NAME", "Staff")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Modèle Claude utilisé pour la génération du résumé.
MODELE_CLAUDE = "claude-sonnet-5"


def est_staff():
    """
    Décorateur de vérification : autorise la commande uniquement si
    l'auteur possède le rôle STAFF_ROLE_NAME (.env), ou s'il est
    administrateur du serveur.
    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        return any(role.name == STAFF_ROLE_NAME for role in ctx.author.roles)
    return commands.check(predicate)


class Infos(commands.Cog):
    """Cog regroupant les commandes d'information sur le serveur et le chat."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # On initialise le client Anthropic une seule fois si possible.
        if ANTHROPIC_DISPONIBLE and ANTHROPIC_API_KEY:
            self.client_claude = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        else:
            self.client_claude = None

    # ------------------------------------------------------------------
    # COMMANDE : !serverstats
    # ------------------------------------------------------------------
    @commands.command(name="serverstats", aliases=["stats"], help="Affiche les statistiques du serveur.")
    @commands.guild_only()
    async def serverstats(self, ctx: commands.Context):
        """Affiche un embed complet avec les statistiques clés du serveur."""
        guild = ctx.guild

        membres_totaux = guild.member_count
        membres_humains = sum(1 for membre in guild.members if not membre.bot)
        nombre_bots = membres_totaux - membres_humains

        embed = discord.Embed(
            title=f"📊 Statistiques de {guild.name}",
            color=discord.Color.blurple(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Fondateur", value=str(guild.owner), inline=True)
        embed.add_field(name="📅 Créé le", value=f"{guild.created_at:%d/%m/%Y}", inline=True)
        embed.add_field(name="🆔 ID du serveur", value=str(guild.id), inline=True)

        embed.add_field(name="👥 Membres", value=f"{membres_totaux} (dont {nombre_bots} bots)", inline=True)
        embed.add_field(name="🗣️ Salons texte", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="🔊 Salons vocaux", value=str(len(guild.voice_channels)), inline=True)

        embed.add_field(name="🎭 Rôles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)), inline=True)
        embed.add_field(
            name="🚀 Niveau de boost",
            value=f"Niveau {guild.premium_tier} ({guild.premium_subscription_count} boosts)",
            inline=True,
        )

        embed.set_footer(text="Kōtei 🍥")
        await ctx.reply(embed=embed, mention_author=False)

    # ------------------------------------------------------------------
    # COMMANDE : !resume (Staff uniquement)
    # ------------------------------------------------------------------
    @commands.command(name="resume", help="[Staff uniquement] Résume les 50 derniers messages du salon.")
    @est_staff()
    @commands.guild_only()
    async def resume(self, ctx: commands.Context):
        """
        Récupère les 50 derniers messages du salon et en génère un résumé
        automatique via l'API Anthropic (Claude). Si l'API n'est pas
        configurée, un résumé statistique simple est généré à la place.
        """
        async with ctx.typing():
            # On récupère l'historique, en excluant la commande !resume elle-même
            # et les messages des bots (bruit non pertinent pour un résumé).
            historique = [
                message async for message in ctx.channel.history(limit=51)
                if message.id != ctx.message.id and not message.author.bot
            ]
            historique.reverse()  # ordre chronologique (du plus ancien au plus récent)

            if not historique:
                await ctx.reply("⚠️ Pas assez de messages récents à résumer dans ce salon.", mention_author=False)
                return

            # --- CAS 1 : Résumé intelligent via Claude (Anthropic) ---
            if self.client_claude is not None:
                transcript = "\n".join(
                    f"{message.author.display_name}: {message.content}"
                    for message in historique
                    if message.content  # on ignore les messages vides (images seules, etc.)
                )

                try:
                    reponse = await self.client_claude.messages.create(
                        model=MODELE_CLAUDE,
                        max_tokens=400,
                        system=(
                            "Tu es un assistant qui résume des conversations Discord en français. "
                            "Fais un résumé clair, neutre et concis en 4 à 6 lignes maximum, "
                            "en dégageant les sujets principaux abordés et les décisions prises."
                        ),
                        messages=[{"role": "user", "content": transcript}],
                    )
                    texte_resume = reponse.content[0].text

                    embed = discord.Embed(
                        title=f"📝 Résumé de #{ctx.channel.name}",
                        description=texte_resume,
                        color=discord.Color.gold(),
                    )
                    embed.set_footer(text=f"Basé sur {len(historique)} messages • Généré par Claude • Kōtei 🍥")
                    await ctx.reply(embed=embed, mention_author=False)
                    return

                except Exception as erreur:
                    # En cas d'erreur API (quota, réseau, etc.), on bascule
                    # sur le résumé simple plutôt que de laisser planter la commande.
                    await ctx.send(f"⚠️ Erreur lors de l'appel à l'API Anthropic ({erreur}). Résumé simplifié généré à la place.")

            # --- CAS 2 : Résumé simple (fallback sans API) ---
            compteur_par_auteur = {}
            for message in historique:
                compteur_par_auteur[message.author.display_name] = compteur_par_auteur.get(message.author.display_name, 0) + 1

            membres_actifs = sorted(compteur_par_auteur.items(), key=lambda x: x[1], reverse=True)[:5]
            classement = "\n".join(f"• **{nom}** — {nb} message(s)" for nom, nb in membres_actifs)

            embed = discord.Embed(
                title=f"📝 Résumé (mode simplifié) de #{ctx.channel.name}",
                description=(
                    f"**{len(historique)}** messages analysés.\n\n"
                    f"**Membres les plus actifs :**\n{classement}\n\n"
                    "*ℹ️ Ajoute une clé ANTHROPIC_API_KEY dans le .env pour activer le résumé intelligent par IA.*"
                ),
                color=discord.Color.light_grey(),
            )
            embed.set_footer(text="Kōtei 🍥")

        await ctx.reply(embed=embed, mention_author=False)

    @resume.error
    async def resume_error(self, ctx: commands.Context, erreur):
        if isinstance(erreur, commands.CheckFailure):
            await ctx.reply(f"🚫 Cette commande est réservée au rôle **{STAFF_ROLE_NAME}** (ou aux administrateurs).", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Infos(bot))
