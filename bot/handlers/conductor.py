"""
handlers/conductor.py
=====================
Flujos del conductor:
  - /hoy  →  Ver servicios del día asignados
  - /salida  →  Confirmar salida (PROGRAMADO → EN_CURSO)
  - /llegada →  Confirmar llegada (registra hora_llegada_real)
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import joinedload
from telegram import Update
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler,
)

from ..database import get_session
from ..middleware import get_usuario
from ..keyboards import servicios_para_accion, volver_menu

from backend.models.servicio import Servicio
from backend.models.ruta import Ruta

# ── Estados de conversación ────────────────────────────────────────────────
ESPERANDO_HORA_LLEGADA = 1


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _formatear_servicio(s: Servicio, modo: str = "completo") -> str:
    """Formatea un servicio como texto Markdown."""
    hora  = s.hora_inicio.strftime("%H:%M") if s.hora_inicio else "--:--"
    ruta  = s.ruta.nombre if s.ruta else f"Ruta #{s.ruta_id}"
    placa = s.vehiculo.placa if s.vehiculo else f"Veh #{s.vehiculo_id}"

    ESTADO_EMOJI = {
        "PROGRAMADO": "🟡",
        "EN_CURSO":   "🟢",
        "COMPLETADO": "✅",
        "CANCELADO":  "🔴",
    }
    emoji = ESTADO_EMOJI.get(s.estado, "⚪")

    if modo == "breve":
        return f"{emoji} [{hora}] {ruta[:35]}"

    llegada_est = (
        s.hora_llegada_est.strftime("%H:%M") if s.hora_llegada_est else "—"
    )
    origen = (
        f"\n📍 Recojo: {s.paradero_origen.nombre}"
        if s.paradero_origen else ""
    )
    obs = f"\n💬 {s.observaciones}" if s.observaciones else ""

    return (
        f"{emoji} *{ruta}*\n"
        f"🕐 Salida: {hora}  |  Llegada est.: {llegada_est}\n"
        f"🚌 Vehículo: {placa}{origen}{obs}\n"
        f"Estado: {s.estado}"
    )


def _servicios_conductor_hoy(conductor_id: int, db) -> list[Servicio]:
    hoy = date.today()
    return (
        db.query(Servicio)
        .options(
            joinedload(Servicio.ruta),
            joinedload(Servicio.vehiculo),
            joinedload(Servicio.paradero_origen),
        )
        .filter(
            Servicio.conductor_id == conductor_id,
            Servicio.fecha == hoy,
            Servicio.estado.notin_(["CANCELADO"]),
        )
        .order_by(Servicio.hora_inicio)
        .all()
    )


# ─────────────────────────────────────────────
# /hoy — Servicios del día
# ─────────────────────────────────────────────
async def cmd_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario:
            await update.message.reply_text("No estás registrado en el sistema.")
            return

        # Conductores ven sus propios servicios; programadores también
        # usan /hoy para ver los suyos si tienen emp_id asignado
        conductor_id = getattr(usuario, "emp_id", None) or usuario.usuario_id
        servicios = _servicios_conductor_hoy(conductor_id, db)

        if not servicios:
            await update.message.reply_text(
                f"📭 No tienes servicios asignados para hoy ({date.today().strftime('%d/%m/%Y')}).",
                reply_markup=volver_menu(),
            )
            return

        lineas = [f"📋 *Tus servicios del {date.today().strftime('%d/%m/%Y')}:*\n"]
        for i, s in enumerate(servicios, start=1):
            lineas.append(f"*{i}.* {_formatear_servicio(s)}\n")

        await update.message.reply_text(
            "\n".join(lineas),
            parse_mode="Markdown",
            reply_markup=volver_menu(),
        )


async def cb_mis_servicios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback del botón 'Mis servicios de hoy'."""
    query = update.callback_query
    await query.answer()
    tid = query.from_user.id

    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario:
            await query.edit_message_text("No estás registrado.")
            return

        conductor_id = getattr(usuario, "emp_id", None) or usuario.usuario_id
        servicios = _servicios_conductor_hoy(conductor_id, db)

        if not servicios:
            await query.edit_message_text(
                f"📭 No tienes servicios asignados para hoy ({date.today().strftime('%d/%m/%Y')}).",
                reply_markup=volver_menu(),
            )
            return

        lineas = [f"📋 *Tus servicios del {date.today().strftime('%d/%m/%Y')}:*\n"]
        for i, s in enumerate(servicios, start=1):
            lineas.append(f"*{i}.* {_formatear_servicio(s)}\n")

        await query.edit_message_text(
            "\n".join(lineas),
            parse_mode="Markdown",
            reply_markup=volver_menu(),
        )


# ─────────────────────────────────────────────
# /salida — Confirmar salida al servicio
# ─────────────────────────────────────────────
async def cmd_salida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario:
            await update.message.reply_text("No estás registrado en el sistema.")
            return

        conductor_id = getattr(usuario, "emp_id", None) or usuario.usuario_id
        servicios = _servicios_conductor_hoy(conductor_id, db)
        pendientes = [s for s in servicios if s.estado == "PROGRAMADO"]

        if not pendientes:
            await update.message.reply_text(
                "✅ No tienes servicios pendientes de salida por ahora.",
                reply_markup=volver_menu(),
            )
            return

        await update.message.reply_text(
            "🚌 *¿Cuál servicio vas a iniciar?*\nSelecciona uno:",
            parse_mode="Markdown",
            reply_markup=servicios_para_accion(pendientes, "salida"),
        )


async def cb_confirmar_salida_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botón del menú principal → igual que /salida."""
    query = update.callback_query
    await query.answer()
    tid = query.from_user.id

    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario:
            await query.edit_message_text("No estás registrado.")
            return

        conductor_id = getattr(usuario, "emp_id", None) or usuario.usuario_id
        servicios = _servicios_conductor_hoy(conductor_id, db)
        pendientes = [s for s in servicios if s.estado == "PROGRAMADO"]

        if not pendientes:
            await query.edit_message_text(
                "✅ No tienes servicios pendientes de salida.",
                reply_markup=volver_menu(),
            )
            return

        await query.edit_message_text(
            "🚌 *¿Cuál servicio vas a iniciar?*",
            parse_mode="Markdown",
            reply_markup=servicios_para_accion(pendientes, "salida"),
        )


async def cb_ejecutar_salida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback cuando el conductor selecciona un servicio para marcar salida."""
    query = update.callback_query
    await query.answer()

    servicio_id = int(query.data.split(":")[1])
    ahora = datetime.now().time()

    with get_session() as db:
        s = db.query(Servicio).filter(Servicio.servicio_id == servicio_id).first()
        if not s:
            await query.edit_message_text("❌ Servicio no encontrado.")
            return
        if s.estado != "PROGRAMADO":
            await query.edit_message_text(
                f"⚠️ Este servicio ya está en estado *{s.estado}*.",
                parse_mode="Markdown",
                reply_markup=volver_menu(),
            )
            return

        s.estado = "EN_CURSO"
        # Registramos la hora real de inicio si se quiere auditar
        # (campo opcional — no está en el schema actual, se puede agregar)

    ruta_nombre = s.ruta.nombre if s.ruta else f"Ruta #{s.ruta_id}"
    await query.edit_message_text(
        f"✅ *¡Salida confirmada!*\n\n"
        f"🚌 {ruta_nombre}\n"
        f"🕐 Hora: {ahora.strftime('%H:%M')}\n\n"
        f"¡Buen viaje! Cuando llegues al destino usa /llegada.",
        parse_mode="Markdown",
        reply_markup=volver_menu(),
    )


# ─────────────────────────────────────────────
# /llegada — Confirmar llegada al destino
# ─────────────────────────────────────────────
async def cmd_llegada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario:
            await update.message.reply_text("No estás registrado en el sistema.")
            return

        conductor_id = getattr(usuario, "emp_id", None) or usuario.usuario_id
        servicios = _servicios_conductor_hoy(conductor_id, db)
        en_curso = [s for s in servicios if s.estado == "EN_CURSO"]

        if not en_curso:
            await update.message.reply_text(
                "🤷 No tienes servicios en curso ahora mismo.",
                reply_markup=volver_menu(),
            )
            return

        await update.message.reply_text(
            "🏁 *¿A qué servicio llegaste?*",
            parse_mode="Markdown",
            reply_markup=servicios_para_accion(en_curso, "llegada"),
        )


async def cb_confirmar_llegada_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = query.from_user.id

    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario:
            await query.edit_message_text("No estás registrado.")
            return

        conductor_id = getattr(usuario, "emp_id", None) or usuario.usuario_id
        servicios = _servicios_conductor_hoy(conductor_id, db)
        en_curso = [s for s in servicios if s.estado == "EN_CURSO"]

        if not en_curso:
            await query.edit_message_text(
                "🤷 No tienes servicios en curso ahora mismo.",
                reply_markup=volver_menu(),
            )
            return

        await query.edit_message_text(
            "🏁 *¿A qué servicio llegaste?*",
            parse_mode="Markdown",
            reply_markup=servicios_para_accion(en_curso, "llegada"),
        )


async def cb_ejecutar_llegada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """El conductor seleccionó el servicio → registrar hora de llegada y completar."""
    query = update.callback_query
    await query.answer()

    servicio_id = int(query.data.split(":")[1])
    ahora = datetime.now()

    with get_session() as db:
        s = db.query(Servicio).options(joinedload(Servicio.ruta)).filter(
            Servicio.servicio_id == servicio_id
        ).first()

        if not s:
            await query.edit_message_text("❌ Servicio no encontrado.")
            return
        if s.estado != "EN_CURSO":
            await query.edit_message_text(
                f"⚠️ Este servicio está en estado *{s.estado}*.",
                parse_mode="Markdown",
                reply_markup=volver_menu(),
            )
            return

        s.hora_llegada_real = ahora.time()
        # Si la llegada es al día siguiente, registrar fecha
        if s.fecha and ahora.date() > s.fecha:
            s.fecha_llegada = ahora.date()
        s.estado = "COMPLETADO"

    ruta_nombre = s.ruta.nombre if s.ruta else f"Ruta #{s.ruta_id}"
    await query.edit_message_text(
        f"✅ *¡Llegada confirmada!*\n\n"
        f"🏁 {ruta_nombre}\n"
        f"🕐 Hora: {ahora.strftime('%H:%M')}\n\n"
        f"Servicio marcado como *COMPLETADO*. ¡Gracias!",
        parse_mode="Markdown",
        reply_markup=volver_menu(),
    )


# ─── Registro de handlers ────────────────────────────────────────────────────
def register(app):
    app.add_handler(CommandHandler("hoy",     cmd_hoy))
    app.add_handler(CommandHandler("salida",  cmd_salida))
    app.add_handler(CommandHandler("llegada", cmd_llegada))

    app.add_handler(CallbackQueryHandler(cb_mis_servicios,          pattern="^mis_servicios$"))
    app.add_handler(CallbackQueryHandler(cb_confirmar_salida_menu,  pattern="^confirmar_salida$"))
    app.add_handler(CallbackQueryHandler(cb_confirmar_llegada_menu, pattern="^confirmar_llegada$"))
    app.add_handler(CallbackQueryHandler(cb_ejecutar_salida,        pattern="^salida:\\d+$"))
    app.add_handler(CallbackQueryHandler(cb_ejecutar_llegada,       pattern="^llegada:\\d+$"))
