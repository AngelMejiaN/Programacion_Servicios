"""
handlers/start.py
=================
Maneja /start, /ayuda y el botón "menu" (volver al menú principal).
"""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from ..database import get_session
from ..middleware import get_usuario, es_programador
from ..keyboards import menu_conductor, menu_programador, volver_menu

BIENVENIDA_NO_REGISTRADO = (
    "👋 Hola, soy el bot de *TransitPro*.\n\n"
    "Parece que aún no estás registrado en el sistema.\n"
    "Comunícate con tu administrador para que te agregue "
    "con tu ID de Telegram: `{tid}`"
)

AYUDA_CONDUCTOR = (
    "📖 *Comandos disponibles:*\n\n"
    "/start — Menú principal\n"
    "/hoy — Ver mis servicios de hoy\n"
    "/salida — Confirmar que salí al servicio\n"
    "/llegada — Confirmar que llegué al destino\n"
    "/ayuda — Esta ayuda"
)

AYUDA_PROGRAMADOR = (
    "📖 *Comandos disponibles:*\n\n"
    "/start — Menú principal\n"
    "/hoy — Ver mis servicios de hoy\n"
    "/resumen — Programación completa del día\n"
    "/nuevo — Crear un nuevo servicio\n"
    "/salida — Confirmar salida de un servicio\n"
    "/llegada — Confirmar llegada de un servicio\n"
    "/ayuda — Esta ayuda"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    nombre = update.effective_user.first_name or "allí"

    with get_session() as db:
        usuario = get_usuario(tid, db)

    if not usuario:
        await update.message.reply_text(
            BIENVENIDA_NO_REGISTRADO.format(tid=tid),
            parse_mode="Markdown",
        )
        return

    saludo = f"👋 Hola, *{usuario.nombre}*! ¿Qué necesitas hoy?"

    if es_programador(usuario):
        await update.message.reply_text(
            saludo,
            parse_mode="Markdown",
            reply_markup=menu_programador(),
        )
    else:
        await update.message.reply_text(
            saludo,
            parse_mode="Markdown",
            reply_markup=menu_conductor(),
        )


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    with get_session() as db:
        usuario = get_usuario(tid, db)

    if not usuario:
        await update.message.reply_text(
            "No estás registrado. Habla con tu administrador.",
        )
        return

    texto = AYUDA_PROGRAMADOR if es_programador(usuario) else AYUDA_CONDUCTOR
    await update.message.reply_text(texto, parse_mode="Markdown")


async def cb_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback del botón 'Volver al menú'."""
    query = update.callback_query
    await query.answer()
    tid = query.from_user.id

    with get_session() as db:
        usuario = get_usuario(tid, db)

    if not usuario:
        await query.edit_message_text("No estás registrado.")
        return

    saludo = f"👋 ¿Qué más necesitas, *{usuario.nombre}*?"
    markup = menu_programador() if es_programador(usuario) else menu_conductor()
    await query.edit_message_text(saludo, parse_mode="Markdown", reply_markup=markup)


async def cb_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback del botón '❌ Cancelar' — limpia contexto y vuelve al menú."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()

    tid = query.from_user.id
    with get_session() as db:
        usuario = get_usuario(tid, db)

    markup = menu_programador() if (usuario and es_programador(usuario)) else menu_conductor()
    await query.edit_message_text(
        "Operación cancelada. ¿Qué más necesitas?",
        reply_markup=markup,
    )


# ─── Registro de handlers ────────────────────────────────────────────────────
def register(app):
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("ayuda",  cmd_ayuda))
    app.add_handler(CallbackQueryHandler(cb_menu,     pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(cb_cancelar, pattern="^cancelar$"))
