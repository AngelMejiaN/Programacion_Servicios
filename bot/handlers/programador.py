"""
handlers/programador.py
=======================
Flujos del programador — versión simplificada:
  /resumen  →  Programación del día
  /nuevo    →  Crear servicio (4 pasos: fecha → ruta → vehículo+conductor → hora)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import joinedload
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters,
)

from ..database import get_session
from ..middleware import get_usuario, es_programador
from ..keyboards import lista_paginada, volver_menu

from backend.models.servicio import Servicio
from backend.models.ruta import Ruta
from backend.models.vehiculo import Vehiculo
from backend.services.conductores import get_conductores_by_sede
from backend.services.programacion import validar_y_enriquecer
from backend.schemas.servicio import ServicioCreate

# ── Estados de la conversación ─────────────────────────────────────────────
NV_FECHA, NV_RUTA, NV_VEHICULO, NV_CONDUCTOR, NV_HORA, NV_CONFIRMAR = range(6)
CANCELAR_CONV = ConversationHandler.END

ESTADO_EMOJI = {"PROGRAMADO": "🟡", "EN_CURSO": "🟢", "COMPLETADO": "✅", "CANCELADO": "🔴"}


# ─────────────────────────────────────────────
# RESUMEN DEL DÍA
# ─────────────────────────────────────────────
async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tid = update.effective_user.id
    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario or not es_programador(usuario):
            await update.message.reply_text("No tienes permisos para ver el resumen.")
            return
        hoy = date.today()
        servicios = (
            db.query(Servicio)
            .options(joinedload(Servicio.ruta), joinedload(Servicio.vehiculo))
            .filter(Servicio.sede_id == usuario.sede_id, Servicio.fecha == hoy)
            .order_by(Servicio.hora_inicio)
            .all()
        )
        sede_id = usuario.sede_id

    titulo = f"📅 *Programación {hoy.strftime('%d/%m/%Y')}*\n"
    if not servicios:
        texto = titulo + "\n📭 No hay servicios programados para hoy."
    else:
        lineas = [titulo]
        for s in servicios:
            emoji = ESTADO_EMOJI.get(s.estado, "⚪")
            hora  = s.hora_inicio.strftime("%H:%M") if s.hora_inicio else "--:--"
            ruta  = (s.ruta.nombre[:35] if s.ruta else f"Ruta #{s.ruta_id}")
            placa = (s.vehiculo.placa if s.vehiculo else f"#{s.vehiculo_id}")
            lineas.append(f"{emoji} `{hora}` {ruta} · {placa}")
        total = len(servicios)
        prog  = sum(1 for s in servicios if s.estado == "PROGRAMADO")
        cur   = sum(1 for s in servicios if s.estado == "EN_CURSO")
        comp  = sum(1 for s in servicios if s.estado == "COMPLETADO")
        lineas.append(f"\n📊 Total: {total}  🟡{prog}  🟢{cur}  ✅{comp}")
        texto = "\n".join(lineas)

    await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=volver_menu())


async def cb_resumen_dia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = query.from_user.id
    with get_session() as db:
        usuario = get_usuario(tid, db)
        if not usuario or not es_programador(usuario):
            await query.edit_message_text("No tienes permisos.")
            return
        hoy = date.today()
        servicios = (
            db.query(Servicio)
            .options(joinedload(Servicio.ruta), joinedload(Servicio.vehiculo))
            .filter(Servicio.sede_id == usuario.sede_id, Servicio.fecha == hoy)
            .order_by(Servicio.hora_inicio)
            .all()
        )

    titulo = f"📅 *Programación {hoy.strftime('%d/%m/%Y')}*\n"
    if not servicios:
        texto = titulo + "\n📭 No hay servicios programados."
    else:
        lineas = [titulo]
        for s in servicios:
            emoji = ESTADO_EMOJI.get(s.estado, "⚪")
            hora  = s.hora_inicio.strftime("%H:%M") if s.hora_inicio else "--:--"
            ruta  = (s.ruta.nombre[:35] if s.ruta else f"Ruta #{s.ruta_id}")
            lineas.append(f"{emoji} `{hora}` {ruta}")
        total = len(servicios)
        prog  = sum(1 for s in servicios if s.estado == "PROGRAMADO")
        cur   = sum(1 for s in servicios if s.estado == "EN_CURSO")
        comp  = sum(1 for s in servicios if s.estado == "COMPLETADO")
        lineas.append(f"\n📊 {total} servicios  🟡{prog}  🟢{cur}  ✅{comp}")
        texto = "\n".join(lineas)

    await query.edit_message_text(texto, parse_mode="Markdown", reply_markup=volver_menu())


# ─────────────────────────────────────────────
# CREAR SERVICIO — flujo simplificado (4 pasos)
# ─────────────────────────────────────────────

def _teclado_fechas() -> InlineKeyboardMarkup:
    hoy    = date.today()
    manana = hoy + timedelta(days=1)
    pasado = hoy + timedelta(days=2)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Hoy ({hoy.strftime('%d/%m')})",      callback_data=f"nv_fecha:{hoy.isoformat()}"),
            InlineKeyboardButton(f"Mañana ({manana.strftime('%d/%m')})", callback_data=f"nv_fecha:{manana.isoformat()}"),
        ],
        [
            InlineKeyboardButton(f"{pasado.strftime('%d/%m')}",         callback_data=f"nv_fecha:{pasado.isoformat()}"),
            InlineKeyboardButton("📅 Otra fecha (DD/MM)",               callback_data="nv_fecha:manual"),
        ],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
    ])


def _teclado_horas() -> InlineKeyboardMarkup:
    horas = ["04:00","05:00","05:30","06:00","06:30","07:00","08:00","09:00"]
    filas = []
    for i in range(0, len(horas), 4):
        filas.append([
            InlineKeyboardButton(h, callback_data=f"nv_hora:{h}")
            for h in horas[i:i+4]
        ])
    filas.append([InlineKeyboardButton("⌨️ Escribir hora (HH:MM)", callback_data="nv_hora:manual")])
    filas.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    return InlineKeyboardMarkup(filas)


async def nv_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entrada: /nuevo o botón 'Crear servicio'."""
    tid = update.effective_user.id if update.message else update.callback_query.from_user.id

    with get_session() as db:
        usuario = get_usuario(tid, db)

    if not usuario or not es_programador(usuario):
        texto = "❌ No tienes permisos para crear servicios."
        if update.message:
            await update.message.reply_text(texto)
        else:
            await update.callback_query.edit_message_text(texto)
        return CANCELAR_CONV

    # Limpiar estado anterior
    context.user_data.clear()
    context.user_data["sede_id"]    = usuario.sede_id
    context.user_data["usuario_id"] = usuario.usuario_id

    texto = (
        "➕ *Nuevo servicio*\n\n"
        f"Sede: *{usuario.sede_id}*\n\n"
        "Paso 1/4 — ¿Para qué fecha?"
    )
    if update.message:
        await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=_teclado_fechas())
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(texto, parse_mode="Markdown", reply_markup=_teclado_fechas())

    return NV_FECHA


async def nv_fecha_boton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Selección de fecha con botón."""
    query = update.callback_query
    await query.answer()
    valor = query.data.split(":", 1)[1]

    if valor == "manual":
        await query.edit_message_text(
            "📅 Escribe la fecha en formato *DD/MM/YYYY*:",
            parse_mode="Markdown",
        )
        context.user_data["esperando_fecha_manual"] = True
        return NV_FECHA

    context.user_data["fecha"] = valor
    context.user_data.pop("esperando_fecha_manual", None)
    return await _mostrar_rutas(query, context)


async def nv_fecha_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Fecha escrita manualmente."""
    texto = update.message.text.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            fecha = datetime.strptime(texto, fmt).date()
            context.user_data["fecha"] = fecha.isoformat()
            context.user_data.pop("esperando_fecha_manual", None)
            # Crear un objeto simulado para reutilizar _mostrar_rutas
            await update.message.reply_text(
                f"✅ Fecha: *{fecha.strftime('%d/%m/%Y')}*\n\nCargando rutas...",
                parse_mode="Markdown"
            )
            return await _mostrar_rutas_msg(update, context)
        except ValueError:
            pass
    await update.message.reply_text(
        "⚠️ Formato no válido. Escribe la fecha como *DD/MM/YYYY*:",
        parse_mode="Markdown",
    )
    return NV_FECHA


async def _mostrar_rutas(query, context) -> int:
    sede_id = context.user_data["sede_id"]
    fecha_str = context.user_data["fecha"]
    with get_session() as db:
        rutas = (
            db.query(Ruta)
            .filter(Ruta.sede_id == sede_id, Ruta.activa == True)
            .order_by(Ruta.nombre)
            .all()
        )
        items = [(f"[{r.ruta_id}] {r.nombre[:40]}", f"nv_ruta:{r.ruta_id}") for r in rutas]

    context.user_data["rutas_items"] = items
    fecha_display = datetime.fromisoformat(fecha_str).strftime("%d/%m/%Y")

    if not items:
        await query.edit_message_text("❌ No hay rutas disponibles para esta sede.")
        return CANCELAR_CONV

    await query.edit_message_text(
        f"📅 Fecha: *{fecha_display}*\n\n"
        "Paso 2/4 — Selecciona la *ruta*:",
        parse_mode="Markdown",
        reply_markup=lista_paginada(items, pagina=0, prefijo_nav="pag_ruta"),
    )
    return NV_RUTA


async def _mostrar_rutas_msg(update, context) -> int:
    sede_id = context.user_data["sede_id"]
    fecha_str = context.user_data["fecha"]
    with get_session() as db:
        rutas = (
            db.query(Ruta)
            .filter(Ruta.sede_id == sede_id, Ruta.activa == True)
            .order_by(Ruta.nombre)
            .all()
        )
        items = [(f"[{r.ruta_id}] {r.nombre[:40]}", f"nv_ruta:{r.ruta_id}") for r in rutas]

    context.user_data["rutas_items"] = items
    fecha_display = datetime.fromisoformat(fecha_str).strftime("%d/%m/%Y")

    if not items:
        await update.message.reply_text("❌ No hay rutas disponibles para esta sede.")
        return CANCELAR_CONV

    await update.message.reply_text(
        f"📅 Fecha: *{fecha_display}*\n\n"
        "Paso 2/4 — Selecciona la *ruta*:",
        parse_mode="Markdown",
        reply_markup=lista_paginada(items, pagina=0, prefijo_nav="pag_ruta"),
    )
    return NV_RUTA


async def nv_paginar_rutas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    pagina = int(query.data.split(":")[1])
    items  = context.user_data.get("rutas_items", [])
    await query.edit_message_reply_markup(
        reply_markup=lista_paginada(items, pagina=pagina, prefijo_nav="pag_ruta")
    )
    return NV_RUTA


async def nv_recibir_ruta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ruta_id = int(query.data.split(":")[1])
    context.user_data["ruta_id"] = ruta_id

    sede_id = context.user_data["sede_id"]
    with get_session() as db:
        ruta = db.query(Ruta).filter(Ruta.ruta_id == ruta_id).first()
        context.user_data["ruta_nombre"]              = ruta.nombre if ruta else str(ruta_id)
        context.user_data["requiere_dos_conductores"] = bool(ruta.requiere_dos_conductores) if ruta else False

        vehiculos = (
            db.query(Vehiculo)
            .filter(Vehiculo.sede_id == sede_id, Vehiculo.operativo == True)
            .order_by(Vehiculo.placa)
            .all()
        )
        conductores = get_conductores_by_sede(sede_id, db)

    if not vehiculos:
        await query.edit_message_text("❌ No hay vehículos operativos en esta sede.")
        return CANCELAR_CONV
    if not conductores:
        await query.edit_message_text("❌ No hay conductores disponibles en esta sede.")
        return CANCELAR_CONV

    # Mostrar vehículos y conductores juntos (Paso 3)
    veh_items   = [(f"🚌 {v.placa} — {v.marca} {v.modelo}", f"nv_veh:{v.vehiculo_id}") for v in vehiculos]
    cond_items  = [(f"👤 {c['nombre_completo']}", f"nv_cond:{c['emp_id']}") for c in conductores]

    context.user_data["veh_items"]  = veh_items
    context.user_data["cond_items"] = cond_items

    await query.edit_message_text(
        f"🛣️ Ruta: *{context.user_data['ruta_nombre'][:45]}*\n\n"
        "Paso 3a/4 — Selecciona el *vehículo*:",
        parse_mode="Markdown",
        reply_markup=lista_paginada(veh_items, pagina=0, prefijo_nav="pag_veh"),
    )
    return NV_VEHICULO


async def nv_paginar_vehiculos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    pagina = int(query.data.split(":")[1])
    items  = context.user_data.get("veh_items", [])
    await query.edit_message_reply_markup(
        reply_markup=lista_paginada(items, pagina=pagina, prefijo_nav="pag_veh")
    )
    return NV_VEHICULO


async def nv_recibir_vehiculo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    veh_id = int(query.data.split(":")[1])
    context.user_data["vehiculo_id"] = veh_id

    with get_session() as db:
        v = db.query(Vehiculo).filter(Vehiculo.vehiculo_id == veh_id).first()
        context.user_data["placa"] = v.placa if v else str(veh_id)

    cond_items = context.user_data.get("cond_items", [])
    await query.edit_message_text(
        f"🚌 Vehículo: *{context.user_data['placa']}*\n\n"
        "Paso 3b/4 — Selecciona el *conductor*:",
        parse_mode="Markdown",
        reply_markup=lista_paginada(cond_items, pagina=0, prefijo_nav="pag_cond"),
    )
    return NV_CONDUCTOR


async def nv_paginar_conductores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    pagina = int(query.data.split(":")[1])
    items  = context.user_data.get("cond_items", [])
    await query.edit_message_reply_markup(
        reply_markup=lista_paginada(items, pagina=pagina, prefijo_nav="pag_cond")
    )
    return NV_CONDUCTOR


async def nv_recibir_conductor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cond_id = int(query.data.split(":")[1])
    context.user_data["conductor_id"] = cond_id

    # Buscar nombre
    cond_items = context.user_data.get("cond_items", [])
    nombre = next((lbl for lbl, cb in cond_items if cb == f"nv_cond:{cond_id}"), str(cond_id))
    context.user_data["conductor_nombre"] = nombre.replace("👤 ", "")

    await query.edit_message_text(
        f"🚌 *{context.user_data['placa']}*  |  👤 *{context.user_data['conductor_nombre']}*\n\n"
        "Paso 4/4 — ¿A qué hora sale el servicio?",
        parse_mode="Markdown",
        reply_markup=_teclado_horas(),
    )
    return NV_HORA


async def nv_hora_boton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    valor = query.data.split(":", 1)[1]

    if valor == "manual":
        await query.edit_message_text(
            "⌨️ Escribe la hora en formato *HH:MM* (ej: 06:30):",
            parse_mode="Markdown",
        )
        context.user_data["esperando_hora_manual"] = True
        return NV_HORA

    context.user_data["hora_inicio"] = valor
    return await _mostrar_resumen(query, context)


async def nv_hora_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    try:
        datetime.strptime(texto, "%H:%M")
        context.user_data["hora_inicio"] = texto
        context.user_data.pop("esperando_hora_manual", None)
        await update.message.reply_text("✅ Hora registrada. Preparando resumen...")
        return await _mostrar_resumen_msg(update, context)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Formato incorrecto. Escribe la hora como *HH:MM* (ej: 06:30):",
            parse_mode="Markdown",
        )
        return NV_HORA


async def _mostrar_resumen(query, context) -> int:
    datos = context.user_data
    fecha_display = datetime.fromisoformat(datos["fecha"]).strftime("%d/%m/%Y")
    resumen = (
        "📋 *Resumen del nuevo servicio:*\n\n"
        f"📅 Fecha: *{fecha_display}*\n"
        f"🛣️ Ruta: {datos['ruta_nombre'][:45]}\n"
        f"🚌 Vehículo: *{datos['placa']}*\n"
        f"👤 Conductor: {datos['conductor_nombre']}\n"
        f"🕐 Hora de salida: *{datos['hora_inicio']}*\n\n"
        "¿Confirmas la creación?"
    )
    await query.edit_message_text(
        resumen,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="nv_confirmar"),
                InlineKeyboardButton("❌ Cancelar",  callback_data="cancelar"),
            ]
        ]),
    )
    return NV_CONFIRMAR


async def _mostrar_resumen_msg(update, context) -> int:
    datos = context.user_data
    fecha_display = datetime.fromisoformat(datos["fecha"]).strftime("%d/%m/%Y")
    resumen = (
        "📋 *Resumen del nuevo servicio:*\n\n"
        f"📅 Fecha: *{fecha_display}*\n"
        f"🛣️ Ruta: {datos['ruta_nombre'][:45]}\n"
        f"🚌 Vehículo: *{datos['placa']}*\n"
        f"👤 Conductor: {datos['conductor_nombre']}\n"
        f"🕐 Hora de salida: *{datos['hora_inicio']}*\n\n"
        "¿Confirmas la creación?"
    )
    await update.message.reply_text(
        resumen,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="nv_confirmar"),
                InlineKeyboardButton("❌ Cancelar",  callback_data="cancelar"),
            ]
        ]),
    )
    return NV_CONFIRMAR


async def nv_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    datos = context.user_data

    # Verificar que todos los datos necesarios estén presentes
    requeridos = ["fecha", "ruta_id", "vehiculo_id", "conductor_id", "hora_inicio", "sede_id", "usuario_id"]
    faltantes = [k for k in requeridos if k not in datos]
    if faltantes:
        await query.edit_message_text(
            "⚠️ El proceso fue interrumpido. Por favor usa /nuevo para empezar de nuevo.",
            reply_markup=volver_menu(),
        )
        context.user_data.clear()
        return CANCELAR_CONV

    with get_session() as db:
        ruta = (
            db.query(Ruta)
            .options(joinedload(Ruta.sede))
            .filter(Ruta.ruta_id == datos["ruta_id"], Ruta.activa == True)
            .first()
        )
        if not ruta:
            await query.edit_message_text("❌ Ruta no encontrada.", reply_markup=volver_menu())
            return CANCELAR_CONV

        hora_inicio = datetime.strptime(datos["hora_inicio"], "%H:%M").time()

        schema_data = ServicioCreate(
            fecha        = date.fromisoformat(datos["fecha"]),
            sede_id      = datos["sede_id"],
            ruta_id      = datos["ruta_id"],
            vehiculo_id  = datos["vehiculo_id"],
            conductor_id = datos["conductor_id"],
            hora_inicio  = hora_inicio,
        )

        try:
            extras = validar_y_enriquecer(schema_data, ruta, db)
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error de validación:\n{e}",
                reply_markup=volver_menu(),
            )
            return CANCELAR_CONV

        servicio_data = schema_data.model_dump()
        servicio_data.update(extras)
        servicio_data["creado_por"] = datos["usuario_id"]
        servicio_data["estado"]     = "PROGRAMADO"

        servicio = Servicio(**servicio_data)
        db.add(servicio)
        db.flush()
        sid = servicio.servicio_id

    fecha_display = datetime.fromisoformat(datos["fecha"]).strftime("%d/%m/%Y")
    context.user_data.clear()

    await query.edit_message_text(
        f"✅ *¡Servicio #{sid} creado!*\n\n"
        f"📅 {fecha_display}  🕐 {datos['hora_inicio']}\n"
        f"🛣️ {datos['ruta_nombre'][:45]}",
        parse_mode="Markdown",
        reply_markup=volver_menu(),
    )
    return CANCELAR_CONV


async def nv_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    if update.message:
        await update.message.reply_text("Operación cancelada.", reply_markup=volver_menu())
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Operación cancelada.", reply_markup=volver_menu())
    return CANCELAR_CONV


# ─── Registro de handlers ────────────────────────────────────────────────────
def register(app):
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(CallbackQueryHandler(cb_resumen_dia, pattern="^resumen_dia$"))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("nuevo", nv_inicio),
            CallbackQueryHandler(nv_inicio, pattern="^crear_servicio$"),
        ],
        states={
            NV_FECHA: [
                CallbackQueryHandler(nv_fecha_boton, pattern="^nv_fecha:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, nv_fecha_texto),
            ],
            NV_RUTA: [
                CallbackQueryHandler(nv_recibir_ruta,    pattern="^nv_ruta:\\d+$"),
                CallbackQueryHandler(nv_paginar_rutas,   pattern="^pag_ruta:\\d+$"),
            ],
            NV_VEHICULO: [
                CallbackQueryHandler(nv_recibir_vehiculo,  pattern="^nv_veh:\\d+$"),
                CallbackQueryHandler(nv_paginar_vehiculos, pattern="^pag_veh:\\d+$"),
            ],
            NV_CONDUCTOR: [
                CallbackQueryHandler(nv_recibir_conductor,  pattern="^nv_cond:\\d+$"),
                CallbackQueryHandler(nv_paginar_conductores,pattern="^pag_cond:\\d+$"),
            ],
            NV_HORA: [
                CallbackQueryHandler(nv_hora_boton, pattern="^nv_hora:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, nv_hora_texto),
            ],
            NV_CONFIRMAR: [
                CallbackQueryHandler(nv_confirmar, pattern="^nv_confirmar$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", nv_cancelar),
            CallbackQueryHandler(nv_cancelar, pattern="^cancelar$"),
        ],
        allow_reentry=True,
        per_message=False,
    )
    app.add_handler(conv_handler)
