"""
================================================================
   COG : antispam.py
----------------------------------------------------------------
Automod léger : détecte un membre qui envoie trop de messages en
trop peu de temps, supprime le message en trop, le rend muet
automatiquement, et journalise l'action.

Configuration (.env) :
  - ANTISPAM_SEUIL             → nombre de messages déclenchant l'alerte (défaut : 5)
  - ANTISPAM_FENETRE_SECONDES  → fenêtre de temps observée (défaut : 5s)
  - ANTISPAM_MUTE_MINUTES      → durée du mute automatique (défaut : 10 min)

Les membres ayant la permission "Gérer les messages" sont exemptés
(le staff n'est jamais sanctionné par erreur).
================================================================
"""

import os
import time
import datetime
from collections import defaultdict, deque

import discord
from discord.ext import commands

from . import _modlog

SEUIL = int(os.getenv("ANTISPAM_SEUIL", "5"))
FENETRE_SECONDES = int(os.getenv("ANTISPAM_FENETRE_SECONDES", "5"))
MUTE_MINUTES = int(os.getenv("ANTISPAM_MUTE_MINUTES", "10"))


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

        cle = (message.guild.id, message.author.id)
        maintenant = time.time()
        self.historique[cle].append(maintenant)

        # On ne garde que les horodatages dans la fenêtre de temps observée.
        limite = maintenant - FENETRE_SECONDES
        while self.historique[cle] and self.historique[cle][0] < limite:
            self.historique[cle].popleft()

        if len(self.historique[cle]) < SEUIL:
            return  # pas encore de spam détecté

        # --- Spam détecté : on agit ---
        self.historique[cle].clear()  # on évite de re-déclencher en boucle

        try:
            await message.delete()
        except discord.NotFound:
            pass

        try:
            await message.author.timeout(
                datetime.timedelta(minutes=MUTE_MINUTES),
                reason="Anti-spam automatique",
            )
        except discord.Forbidden:
            pass  # le bot n'a pas les permissions nécessaires sur ce membre

        alerte = await message.channel.send(
            f"🚫 {message.author.mention} a été mis en sourdine {MUTE_MINUTES} min pour spam."
        )
        await alerte.delete(delay=8)

        await _modlog.envoyer_log(
            self.bot,
            titre="🚫 Anti-spam déclenché",
            description=f"{message.author.mention} a envoyé {SEUIL}+ messages en {FENETRE_SECONDES}s dans {message.channel.mention}.",
            couleur=discord.Color.red(),
            champs={"Mute appliqué": f"{MUTE_MINUTES} min"},
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))
