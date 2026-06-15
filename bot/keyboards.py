"""
keyboards.py
============
Teclados inline reutilizables para los handlers del bot.
"""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ─────────────────────────────────────────────
# Menú principal según rol
# ─────────────────────────────────────────────
def menu_conductor() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Mis servicios de hoy",    callback_data="mis_servicios")],
        [InlineKeyboardButton("🚌 Confirmar salida",        callback_data="confirmar_salida")],
        [InlineKeyboardButton("🏁 Confirmar llegada",       callback_data="confirmar_llegada")],
    ])


def menu_programador() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Mis servicios de hoy",    callback_data="mis_servicios")],
        [InlineKeyboardButton("📅 Resumen del día",         callback_data="resumen_dia")],
        [InlineKeyboardButton("➕ Crear servicio",          callback_data="crear_servicio")],
        [InlineKeyboardButton("🚌 Confirmar salida",        callback_data="confirmar_salida")],
        [InlineKeyboardButton("🏁 Confirmar llegada",       callback_data="confirmar_llegada")],
    ])


# ─────────────────────────────────────────────
# Selección de servicio (para salida/llegada)
# ─────────────────────────────────────────────
def servicios_para_accion(servicios: list, accion: str) -> InlineKeyboardMarkup:
    """
    Recibe lista de servicios y genera botones para seleccionar uno.
    accion: 'salida' | 'llegada'
    """
    botones = []
    for s in servicios:
        hora = s.hora_inicio.strftime("%H:%M") if s.hora_inicio else "--:--"
        label = f"[{hora}] {s.ruta.nombre[:30] if s.ruta else s.ruta_id}"
        botones.append([
            InlineKeyboardButton(label, callback_data=f"{accion}:{s.servicio_id}")
        ])
    botones.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    return InlineKeyboardMarkup(botones)


# ─────────────────────────────────────────────
# Confirmación Sí / No
# ─────────────────────────────────────────────
def confirmar(datos_extra: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmar", callback_data=f"si:{datos_extra}"),
            InlineKeyboardButton("❌ Cancelar",  callback_data="cancelar"),
        ]
    ])


# ─────────────────────────────────────────────
# Paginación de listas (rutas, vehículos, etc.)
# ─────────────────────────────────────────────
def lista_paginada(
    items: list[tuple[str, str]],   # [(label, callback_data), ...]
    pagina: int = 0,
    por_pagina: int = 5,
    prefijo_nav: str = "pag",
) -> InlineKeyboardMarkup:
    """
    Genera un teclado con los items de la página actual y botones
    ◀ / ▶ para navegar.
    """
    inicio  = pagina * por_pagina
    fin     = inicio + por_pagina
    chunk   = items[inicio:fin]
    total_pags = (len(items) - 1) // por_pagina

    botones = [[InlineKeyboardButton(label, callback_data=cb)] for label, cb in chunk]

    nav = []
    if pagina > 0:
        nav.append(InlineKeyboardButton("◀ Anterior", callback_data=f"{prefijo_nav}:{pagina-1}"))
    if pagina < total_pags:
        nav.append(InlineKeyboardButton("Siguiente ▶", callback_data=f"{prefijo_nav}:{pagina+1}"))
    if nav:
        botones.append(nav)

    botones.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    return InlineKeyboardMarkup(botones)


# ─────────────────────────────────────────────
# Botón de volver al menú
# ─────────────────────────────────────────────
def volver_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Volver al menú", callback_data="menu")]
    ])
