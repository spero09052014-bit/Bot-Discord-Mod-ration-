"""
================================================================
   COG : config.py
----------------------------------------------------------------
Interface de configuration 100% cliquable, directement dans un
salon Discord. Plus besoin de modifier le .env ni de taper le
moindre ID à la main : tout se choisit avec des menus déroulants
(salon, rôle, membre) ou de petits formulaires (nombres).

Commande : /config (ou !config)
Accès    : administrateurs du serveur uniquement

Catégories réglables :
  🛡️ Modération   → rôle Staff, salon de logs, fondateurs
  👋 Bienvenue    → salon de bienvenue/au revoir, rôle automatique
  💡 Suggestions  → salon des suggestions
  🎫 Tickets      → catégorie des tickets de support
  📈 Niveaux (XP) → XP par message, cooldown
  🚫 Anti-spam    → seuil, fenêtre, durée du mute

Chaque réglage est stocké par serveur (data/config.json, via
commands/_config.py) : deux serveurs différents peuvent avoir
deux configurations totalement indépendantes.
================================================================
"""

import discord
from discord.ext import commands

from . import _config

# ----------------------------------------------------------------
# TEXTES DES CATÉGORIES
# ----------------------------------------------------------------
DESCRIPTIONS_CATEGORIES = {
    "moderation": ("🛡️ Modération", "Choisis le rôle Staff, le salon de logs de modération, et les fondateurs (accès à `/staffcheck`)."),
    "bienvenue": ("👋 Bienvenue", "Choisis le salon de bienvenue/au revoir et le rôle donné automatiquement aux nouveaux membres."),
    "suggestions": ("💡 Suggestions", "Choisis le salon où seront postées les suggestions des membres."),
    "tickets": ("🎫 Tickets", "Choisis la catégorie dans laquelle seront créés les salons de tickets."),
    "niveaux": ("📈 Niveaux (XP)", "Règle l'XP gagné par message et le délai minimum entre deux gains d'XP."),
    "antispam": ("🚫 Anti-spam", "Règle le seuil, la fenêtre de temps observée et la durée du mute automatique."),
}


def _libelle_sans_emoji(cle: str) -> str:
    return _config.LIBELLES[cle].split(" ", 1)[1]


def _resume_valeur(id_serveur: int, cle: str) -> str:
    valeur = _config.obtenir_reglage(id_serveur, cle)
    if not valeur:
        return "*non défini*"
    if cle in ("MODLOG_CHANNEL_ID", "WELCOME_CHANNEL_ID", "SUGGESTIONS_CHANNEL_ID", "TICKETS_CATEGORY_ID"):
        return f"<#{valeur}>"
    if cle in ("STAFF_ROLE_ID", "AUTOROLE_ID"):
        return f"<@&{valeur}>"
    if cle == "FOUNDER_IDS":
        ids = [identifiant for identifiant in valeur.split(",") if identifiant]
        return ", ".join(f"<@{identifiant}>" for identifiant in ids) if ids else "*non défini*"
    return f"`{valeur}`"


def embed_menu_principal() -> discord.Embed:
    embed = discord.Embed(
        title="⚙️ Configuration de Kōtei",
        description=(
            "Choisis une catégorie ci-dessous pour configurer le bot **en cliquant**, "
            "directement dans ce salon — plus besoin de taper le moindre ID à la main !"
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Kōtei 🍥 • Réservé aux administrateurs")
    return embed


def embed_categorie(cle_categorie: str) -> discord.Embed:
    titre, description = DESCRIPTIONS_CATEGORIES[cle_categorie]
    embed = discord.Embed(title=titre, description=description, color=discord.Color.blurple())
    embed.set_footer(text="Kōtei 🍥 • Clique sur un menu ou un bouton ci-dessous")
    return embed


def embed_resume(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title=f"👁️ Configuration actuelle — {guild.name}",
        description="Réglages actifs pour ce serveur (définis via `/config`, ou repris du `.env` si non définis).",
        color=discord.Color.blurple(),
    )
    for cle, libelle in _config.LIBELLES.items():
        embed.add_field(name=libelle, value=_resume_valeur(guild.id, cle), inline=True)
    embed.set_footer(text="Kōtei 🍥 • /config pour modifier un réglage")
    return embed


# ----------------------------------------------------------------
# COMPOSANTS RÉUTILISABLES (menus déroulants & boutons)
# ----------------------------------------------------------------
class SalonReglageSelect(discord.ui.ChannelSelect):
    """Menu déroulant permettant de choisir un salon (ou une catégorie) pour un réglage donné."""

    def __init__(self, cle: str, channel_types: list, row: int = 0):
        super().__init__(
            placeholder=f"Choisir : {_libelle_sans_emoji(cle)}",
            channel_types=channel_types,
            min_values=1,
            max_values=1,
            row=row,
        )
        self.cle = cle

    async def callback(self, interaction: discord.Interaction):
        salon = self.values[0]
        _config.definir_reglage(interaction.guild.id, self.cle, str(salon.id))
        await interaction.response.send_message(
            f"✅ **{_libelle_sans_emoji(self.cle)}** réglé sur {salon.mention}.", ephemeral=True
        )


class RoleReglageSelect(discord.ui.RoleSelect):
    """Menu déroulant permettant de choisir un rôle pour un réglage donné."""

    def __init__(self, cle: str, row: int = 0):
        super().__init__(
            placeholder=f"Choisir : {_libelle_sans_emoji(cle)}",
            min_values=1,
            max_values=1,
            row=row,
        )
        self.cle = cle

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        _config.definir_reglage(interaction.guild.id, self.cle, str(role.id))
        await interaction.response.send_message(
            f"✅ **{_libelle_sans_emoji(self.cle)}** réglé sur {role.mention}.", ephemeral=True
        )


class FondateursSelect(discord.ui.UserSelect):
    """Menu déroulant permettant de choisir un ou plusieurs fondateurs (accès à /staffcheck)."""

    def __init__(self, row: int = 0):
        super().__init__(
            placeholder="Choisir : Fondateurs (accès à /staffcheck)",
            min_values=1,
            max_values=25,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction):
        ids = ",".join(str(membre.id) for membre in self.values)
        _config.definir_reglage(interaction.guild.id, "FOUNDER_IDS", ids)
        mentions = ", ".join(membre.mention for membre in self.values)
        await interaction.response.send_message(f"✅ **Fondateurs** réglés : {mentions}.", ephemeral=True)


class BoutonDesactiver(discord.ui.Button):
    """Bouton effaçant un réglage (retour à l'éventuelle valeur du .env, ou désactivé)."""

    def __init__(self, cle: str, row: int = 3):
        super().__init__(
            label=f"🗑️ Désactiver : {_libelle_sans_emoji(cle)}",
            style=discord.ButtonStyle.red,
            row=row,
        )
        self.cle = cle

    async def callback(self, interaction: discord.Interaction):
        _config.definir_reglage(interaction.guild.id, self.cle, "")
        await interaction.response.send_message(f"✅ **{_libelle_sans_emoji(self.cle)}** désactivé.", ephemeral=True)


class BoutonOuvrirModal(discord.ui.Button):
    """Bouton ouvrant un petit formulaire (Modal) pour saisir des valeurs numériques."""

    def __init__(self, label: str, classe_modal, row: int = 0):
        super().__init__(label=label, style=discord.ButtonStyle.blurple, row=row)
        self.classe_modal = classe_modal

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.classe_modal(interaction.guild.id))


# ----------------------------------------------------------------
# FORMULAIRES (Modals) POUR LES RÉGLAGES NUMÉRIQUES
# ----------------------------------------------------------------
class ReglageNiveauxModal(discord.ui.Modal, title="📈 Réglages du système de niveaux (XP)"):
    xp_par_message = discord.ui.TextInput(label="XP gagné par message", placeholder="15", max_length=6)
    cooldown_secondes = discord.ui.TextInput(label="Cooldown entre 2 gains d'XP (secondes)", placeholder="60", max_length=6)

    def __init__(self, id_serveur: int):
        super().__init__()
        self.id_serveur = id_serveur
        self.xp_par_message.default = _config.obtenir_reglage(id_serveur, "XP_PAR_MESSAGE")
        self.cooldown_secondes.default = _config.obtenir_reglage(id_serveur, "XP_COOLDOWN_SECONDES")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            xp = int(self.xp_par_message.value)
            cooldown = int(self.cooldown_secondes.value)
            if xp < 0 or cooldown < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("⚠️ Merci d'entrer uniquement des nombres entiers positifs.", ephemeral=True)
            return

        _config.definir_reglage(self.id_serveur, "XP_PAR_MESSAGE", str(xp))
        _config.definir_reglage(self.id_serveur, "XP_COOLDOWN_SECONDES", str(cooldown))
        await interaction.response.send_message(
            f"✅ **XP par message** : `{xp}` • **Cooldown** : `{cooldown}s`.", ephemeral=True
        )


class ReglageAntispamModal(discord.ui.Modal, title="🚫 Réglages de l'anti-spam"):
    seuil = discord.ui.TextInput(label="Nombre de messages avant sanction", placeholder="5", max_length=4)
    fenetre_secondes = discord.ui.TextInput(label="Fenêtre de temps observée (secondes)", placeholder="5", max_length=4)
    mute_minutes = discord.ui.TextInput(label="Durée du mute automatique (minutes)", placeholder="10", max_length=4)

    def __init__(self, id_serveur: int):
        super().__init__()
        self.id_serveur = id_serveur
        self.seuil.default = _config.obtenir_reglage(id_serveur, "ANTISPAM_SEUIL")
        self.fenetre_secondes.default = _config.obtenir_reglage(id_serveur, "ANTISPAM_FENETRE_SECONDES")
        self.mute_minutes.default = _config.obtenir_reglage(id_serveur, "ANTISPAM_MUTE_MINUTES")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            seuil = int(self.seuil.value)
            fenetre = int(self.fenetre_secondes.value)
            mute = int(self.mute_minutes.value)
            if min(seuil, fenetre, mute) < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("⚠️ Merci d'entrer uniquement des nombres entiers positifs (≥ 1).", ephemeral=True)
            return

        _config.definir_reglage(self.id_serveur, "ANTISPAM_SEUIL", str(seuil))
        _config.definir_reglage(self.id_serveur, "ANTISPAM_FENETRE_SECONDES", str(fenetre))
        _config.definir_reglage(self.id_serveur, "ANTISPAM_MUTE_MINUTES", str(mute))
        await interaction.response.send_message(
            f"✅ **Seuil** : `{seuil}` msg • **Fenêtre** : `{fenetre}s` • **Mute** : `{mute}` min.", ephemeral=True
        )


# ----------------------------------------------------------------
# VUES (Views) — un menu par catégorie, plus le menu principal
# ----------------------------------------------------------------
class VueBase(discord.ui.View):
    """Vue de base : vérifie que seule la personne ayant lancé /config peut interagir."""

    def __init__(self, auteur_id: int):
        super().__init__(timeout=300)
        self.auteur_id = auteur_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.auteur_id:
            await interaction.response.send_message(
                "🚫 Seule la personne ayant lancé `/config` peut utiliser ce menu.", ephemeral=True
            )
            return False
        return True


class VueRetour(VueBase):
    """Vue de base pour les sous-catégories : ajoute un bouton "Retour" vers le menu principal."""

    @discord.ui.button(label="⬅️ Retour au menu", style=discord.ButtonStyle.grey, row=4)
    async def retour(self, interaction: discord.Interaction, bouton: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_menu_principal(), view=VueMenuPrincipal(self.auteur_id))


class VueModeration(VueRetour):
    def __init__(self, auteur_id: int):
        super().__init__(auteur_id)
        self.add_item(RoleReglageSelect("STAFF_ROLE_ID", row=0))
        self.add_item(SalonReglageSelect("MODLOG_CHANNEL_ID", [discord.ChannelType.text], row=1))
        self.add_item(FondateursSelect(row=2))
        self.add_item(BoutonDesactiver("STAFF_ROLE_ID", row=3))
        self.add_item(BoutonDesactiver("MODLOG_CHANNEL_ID", row=3))
        self.add_item(BoutonDesactiver("FOUNDER_IDS", row=3))


class VueBienvenue(VueRetour):
    def __init__(self, auteur_id: int):
        super().__init__(auteur_id)
        self.add_item(SalonReglageSelect("WELCOME_CHANNEL_ID", [discord.ChannelType.text], row=0))
        self.add_item(RoleReglageSelect("AUTOROLE_ID", row=1))
        self.add_item(BoutonDesactiver("WELCOME_CHANNEL_ID", row=2))
        self.add_item(BoutonDesactiver("AUTOROLE_ID", row=2))


class VueSuggestions(VueRetour):
    def __init__(self, auteur_id: int):
        super().__init__(auteur_id)
        self.add_item(SalonReglageSelect("SUGGESTIONS_CHANNEL_ID", [discord.ChannelType.text], row=0))
        self.add_item(BoutonDesactiver("SUGGESTIONS_CHANNEL_ID", row=1))


class VueTickets(VueRetour):
    def __init__(self, auteur_id: int):
        super().__init__(auteur_id)
        self.add_item(SalonReglageSelect("TICKETS_CATEGORY_ID", [discord.ChannelType.category], row=0))
        self.add_item(BoutonDesactiver("TICKETS_CATEGORY_ID", row=1))


class VueNiveaux(VueRetour):
    def __init__(self, auteur_id: int):
        super().__init__(auteur_id)
        self.add_item(BoutonOuvrirModal("✏️ Modifier XP / cooldown", ReglageNiveauxModal, row=0))


class VueAntispam(VueRetour):
    def __init__(self, auteur_id: int):
        super().__init__(auteur_id)
        self.add_item(BoutonOuvrirModal("✏️ Modifier seuil / fenêtre / mute", ReglageAntispamModal, row=0))


class MenuPrincipalSelect(discord.ui.Select):
    """Menu déroulant du message principal listant toutes les catégories configurables."""

    def __init__(self):
        options = [
            discord.SelectOption(label="Modération", description="Rôle Staff, salon de logs, fondateurs", emoji="🛡️", value="moderation"),
            discord.SelectOption(label="Bienvenue", description="Salon de bienvenue, rôle automatique", emoji="👋", value="bienvenue"),
            discord.SelectOption(label="Suggestions", description="Salon des suggestions", emoji="💡", value="suggestions"),
            discord.SelectOption(label="Tickets", description="Catégorie des tickets de support", emoji="🎫", value="tickets"),
            discord.SelectOption(label="Niveaux (XP)", description="XP par message, cooldown", emoji="📈", value="niveaux"),
            discord.SelectOption(label="Anti-spam", description="Seuil, fenêtre, durée du mute", emoji="🚫", value="antispam"),
        ]
        super().__init__(placeholder="📂 Choisis une catégorie à configurer...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        vues_par_categorie = {
            "moderation": VueModeration,
            "bienvenue": VueBienvenue,
            "suggestions": VueSuggestions,
            "tickets": VueTickets,
            "niveaux": VueNiveaux,
            "antispam": VueAntispam,
        }
        categorie = self.values[0]
        vue_cible = vues_par_categorie[categorie](self.view.auteur_id)
        await interaction.response.edit_message(embed=embed_categorie(categorie), view=vue_cible)


class VueMenuPrincipal(VueBase):
    def __init__(self, auteur_id: int):
        super().__init__(auteur_id)
        self.add_item(MenuPrincipalSelect())

    @discord.ui.button(label="👁️ Voir la configuration actuelle", style=discord.ButtonStyle.grey, row=1)
    async def voir_config(self, interaction: discord.Interaction, bouton: discord.ui.Button):
        await interaction.response.edit_message(embed=embed_resume(interaction.guild), view=self)


# ----------------------------------------------------------------
# COG
# ----------------------------------------------------------------
class Config(commands.Cog):
    """Cog exposant la commande /config : assistant de configuration 100% cliquable."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="config",
        help="[Admin] Configure le bot en cliquant, directement dans ce salon.",
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx: commands.Context):
        await ctx.reply(embed=embed_menu_principal(), view=VueMenuPrincipal(ctx.author.id), mention_author=False)

    @config.error
    async def config_error(self, ctx: commands.Context, erreur):
        if isinstance(erreur, commands.MissingPermissions):
            await ctx.reply("🚫 Cette commande est réservée aux **administrateurs** du serveur.", mention_author=False)
        elif isinstance(erreur, commands.NoPrivateMessage):
            await ctx.reply("⚠️ Cette commande fonctionne uniquement sur un serveur.", mention_author=False)
        else:
            await ctx.reply(f"❌ Une erreur est survenue : `{erreur}`", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))
