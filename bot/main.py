"""
TransitPro Bot — Entry Point
============================
Arranca con:
    python -m bot.main

Requiere la variable BOT_TOKEN en el archivo .env.
"""
import logging
from telegram.ext import Application

from .config import settings
from .handlers import start, conductor, programador
from .notifications import register_jobs

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN no configurado. Agrega BOT_TOKEN=... al archivo .env"
        )

    logger.info("Iniciando TransitPro Bot...")

    app = (
        Application.builder()
        .token(settings.bot_token)
        .build()
    )

    # ── Registrar handlers ────────────────────────────────────────────────
    start.register(app)
    conductor.register(app)
    programador.register(app)

    # ── Registrar jobs de notificación ────────────────────────────────────
    register_jobs(app)

    # ── Configurar comandos visibles en el menú de Telegram ──────────────
    from telegram import BotCommand
    import asyncio

    async def set_commands(application):
        await application.bot.set_my_commands([
            BotCommand("start",   "Menú principal"),
            BotCommand("hoy",     "Mis servicios de hoy"),
            BotCommand("salida",  "Confirmar que salí al servicio"),
            BotCommand("llegada", "Confirmar que llegué al destino"),
            BotCommand("resumen", "Programación del día (programadores)"),
            BotCommand("nuevo",   "Crear nuevo servicio (programadores)"),
            BotCommand("ayuda",   "Ayuda y comandos disponibles"),
        ])

    app.post_init = set_commands

    logger.info("Bot listo. Escuchando actualizaciones...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
