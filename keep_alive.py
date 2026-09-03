"""
================================================================
   MINI SERVEUR WEB — keep_alive.py
----------------------------------------------------------------
Sert UNIQUEMENT à répondre aux pings HTTP d'UptimeRobot (ou de
n'importe quel service de ping externe), pour empêcher Render de
mettre le bot en veille après 15 minutes d'inactivité (limite de
son offre gratuite "Web Service").

Ce fichier ne contient AUCUNE commande Discord : il tourne en
parallèle du bot, dans un thread séparé démarré depuis bot.py,
pendant que la boucle asyncio du bot gère Discord de son côté.
================================================================
"""

import os
import threading
from flask import Flask

app = Flask("keep_alive")


@app.route("/")
def accueil():
    """Route appelée toutes les quelques minutes par UptimeRobot."""
    return "✅ Le bot Kōtei 🍥 est en ligne !"


def _lancer_serveur():
    # Render fournit automatiquement le port à utiliser via la
    # variable d'environnement PORT. En local (sans Render), on
    # retombe sur 8080 par défaut.
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def demarrer_keep_alive():
    """
    Démarre le mini serveur Flask dans un thread séparé (daemon),
    pour ne surtout pas bloquer la boucle asyncio principale du bot.
    """
    thread = threading.Thread(target=_lancer_serveur, daemon=True)
    thread.start()
