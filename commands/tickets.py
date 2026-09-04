"""
================================================================
   COG : tickets.py
----------------------------------------------------------------
Système de tickets de support privés. Crée un salon textuel visible
uniquement par le membre concerné et le staff.

Commandes :
  !ticket [raison]  → crée un salon de ticket privé
  !close            → ferme (supprime) le ticket en cours, à utiliser
                       DANS le salon du ticket concerné

Configuration (100% modifiable avec /config → "Tickets" et
"Modération", ou via le .env pour un réglage global de secours) :
  - TICKETS_CATEGORY_ID → catégorie où créer les tickets (obligatoire)
  - Rôle Staff          → a accès à tous les tickets (déjà utilisé par infos.py)
================================================================
"""

import asyncio
import discord
from discord.ext import commands

from . import _config
from .infos import a_le_role_staff


class Tickets(commands.Cog):
    """Cog gérant la création et la fermeture des tickets de support."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ticket", help="Ouvre un salon de support privé.")
    @commands.guild_only()
    async def ticket(self, ctx: commands.Context, *, raison: str = "Aucune raison précisée"):
        tickets_category_id = _config.obtenir_reglage(ctx.guild.id, "TICKETS_CATEGORY_ID")
        if not tickets_category_id.isdigit():
            await ctx.reply("⚠️ Le système de tickets n'est pas configuré. Un administrateur peut le régler avec `/config` → \"Tickets\".", mention_author=False)
            return

        categorie = ctx.guild.get_channel(int(tickets_category_id))
        if categorie is None or not isinstance(categorie, discord.CategoryChannel):
            await ctx.reply("⚠️ La catégorie de tickets configurée est introuvable.", mention_author=False)
            return

        # On évite de créer deux tickets ouverts pour la même personne.
        nom_salon = f"ticket-{ctx.author.name}".lower().replace(" ", "-")
        if discord.utils.get(categorie.text_channels, name=nom_salon):
            await ctx.reply("⚠️ Tu as déjà un ticket ouvert !", mention_author=False)
            return

        staff_role_id = _config.obtenir_reglage(ctx.guild.id, "STAFF_ROLE_ID")
        role_staff = ctx.guild.get_role(int(staff_role_id)) if staff_role_id.isdigit() else None

        # Permissions : privé par défaut, visible seulement par l'auteur + le staff.
        permissions = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        if role_staff:
            permissions[role_staff] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        salon_ticket = await categorie.create_text_channel(nom_salon, overwrites=permissions)

        embed = discord.Embed(
            title="🎫 Nouveau ticket",
            description=f"Bonjour {ctx.author.mention}, le staff va te répondre bientôt.",
            color=discord.Color.teal(),
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.set_footer(text="Utilise !close pour fermer ce ticket • Kōtei 🍥")
        await salon_ticket.send(embed=embed)

        await ctx.reply(f"✅ Ton ticket a été créé : {salon_ticket.mention}", mention_author=False)

    @commands.hybrid_command(name="close", help="Ferme le ticket en cours (à utiliser dans le salon du ticket).")
    @commands.guild_only()
    async def close(self, ctx: commands.Context):
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.reply("⚠️ Cette commande ne fonctionne que dans un salon de ticket.", mention_author=False)
            return

        # Seul l'auteur du ticket ou un membre du staff peut le fermer.
        nom_auteur = ctx.channel.name[len("ticket-"):]
        est_auteur = ctx.author.name.lower().replace(" ", "-") == nom_auteur
        if not est_auteur and not a_le_role_staff(ctx.author):
            await ctx.reply("🚫 Seul l'auteur du ticket ou un membre du staff peut le fermer.", mention_author=False)
            return

        await ctx.reply("🔒 Ce ticket sera supprimé dans 5 secondes...", mention_author=False)
        await asyncio.sleep(5)
        await ctx.channel.delete(reason=f"Ticket fermé par {ctx.author}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
