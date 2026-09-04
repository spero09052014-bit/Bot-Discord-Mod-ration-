"""
================================================================
   COG : antispam.py
----------------------------------------------------------------
Automod léger : détecte un membre qui envoie trop de messages en
trop peu de temps, supprime le message en trop, le rend muet
automatiquement, et journalise l'action.

Configuration (100% modifiable avec /config → "Anti-spam", ou
via le .env pour un réglage global de secours) :
  - ANTISPAM_SEUIL             → nombre de messages déclenchant l'alerte (défaut : 5)
  - ANTISPAM_FENETRE_SECONDES  → fenêtre de temps observée (défaut : 5s)
  - ANTISPAM_MUTE_MINUTES      → durée du mute automatique (défaut : 10 min)

Les membres ayant la permission "Gérer les messages" sont exemptés
(le staff n'est jamais sanctionné par erreur).
================================================================
"""

import time
import datetime
from collections import defaultdict, deque

import discord
from discord.ext import commands

from . import _modlog, _config


class AntiSpam(commands.Cog):
    """Cog de modération automatique contre le flood/spam de messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Historique des horodatages de messages par (id_serveur, id_membre).
        # Une deque bornée évite toute fuite mémoire sur le long terme.
        self.historique = defaultdict(lambda: deque(maxlen=50))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # On ignore les bots, les messages privés, et le staff (exempté).
        if message.author.bot or message.guild is None:
            return
        if message.author.guild_permissions.manage_messages:
            return

        id_serveur = message.guild.id
        seuil = _config.obtenir_reglage_int(id_serveur, "ANTISPAM_SEUIL")
        fenetre_secondes = _config.obtenir_reglage_int(id_serveur, "ANTISPAM_FENETRE_SECONDES")
        mute_minutes = _config.obtenir_reglage_int(id_serveur, "ANTISPAM_MUTE_MINUTES")

        cle = (id_serveur, message.author.id)
        maintenant = time.time()
        self.historique[cle].append(maintenant)

        # On ne garde que les horodatages dans la fenêtre de temps observée.
        limite = maintenant - fenetre_secondes
        while self.historique[cle] and self.historique[cle][0] < limite:
            self.historique[cle].popleft()

        if len(self.historique[cle]) < seuil:
            return  # pas encore de spam détecté

        # --- Spam détecté : on agit ---
        self.historique[cle].clear()  # on évite de re-déclencher en boucle

        try:
            await message.delete()
        except discord.NotFound:
            pass

        try:
            await message.author.timeout(
                datetime.timedelta(minutes=mute_minutes),
                reason="Anti-spam automatique",
            )
        except discord.Forbidden:
            pass  # le bot n'a pas les permissions nécessaires sur ce membre

        alerte = await message.channel.send(
            f"🚫 {message.author.mention} a été mis en sourdine {mute_minutes} min pour spam."
        )
        await alerte.delete(delay=8)

        await _modlog.envoyer_log(
            self.bot,
            id_serveur=id_serveur,
            titre="🚫 Anti-spam déclenché",
            description=f"{message.author.mention} a envoyé {seuil}+ messages en {fenetre_secondes}s dans {message.channel.mention}.",
            couleur=discord.Color.red(),
            champs={"Mute appliqué": f"{mute_minutes} min"},
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))
