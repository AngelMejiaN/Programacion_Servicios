"""
notifications.py
================
Notificaciones automáticas programadas:

  1. 20:00 diario → Envía a cada conductor sus servicios del día siguiente.
  2. 07:00 diario → Avisa a programadores si hay servicios sin conductor.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.orm import joinedload
from telegram.ext import Application

from .database import get_session
from .config import settings

from backend.models.servicio import Servicio
from backend.models.usuario import Usuario

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Job 1 — Notificación nocturna a conductores
# ─────────────────────────────────────────────
async def notificar_conductores(context):
    """
    Se ejecuta cada día a las 20:00 (hora Lima).
    Busca todos los servicios del día siguiente y envía un mensaje
    a cada conductor con sus asignaciones.
    """
    manana = date.today() + timedelta(days=1)
    app: Application = context.application

    with get_session() as db:
        servicios = (
            db.query(Servicio)
            .options(
                joinedload(Servicio.ruta),
                joinedload(Servicio.vehiculo),
            )
            .filter(
                Servicio.fecha == manana,
                Servicio.estado == "PROGRAMADO",
            )
            .all()
        )

        if not servicios:
            logger.info("Notificación conductores: sin servicios para %s", manana)
            return

        # Agrupar por conductor (conductor_id es emp_id de T_EMPLEADOS)
        por_conductor: dict[int, list[Servicio]] = {}
        for s in servicios:
            por_conductor.setdefault(s.conductor_id, []).append(s)
            if s.conductor2_id:
                por_conductor.setdefault(s.conductor2_id, []).append(s)

        # Buscar usuarios registrados con ese emp_id
        # Nota: PG_USUARIO no guarda emp_id directamente.
        # Para la notificación buscamos por sede y rol=conductor.
        # Una mejora futura sería agregar emp_id a PG_USUARIO.
        usuarios_conductor = (
            db.query(Usuario)
            .filter(
                Usuario.rol.in_(["conductor"]),
                Usuario.activo == True,
                Usuario.telegram_id.isnot(None),
            )
            .all()
        )

    for usuario in usuarios_conductor:
        # Enviar todos los servicios del día siguiente al conductor
        # (filtrando por los que le corresponden si hay emp_id)
        lineas = [f"🌙 *Tus servicios para mañana {manana.strftime('%d/%m/%Y')}:*\n"]
        encontrado = False

        for emp_id, ss in por_conductor.items():
            # Si el usuario tiene emp_id configurado en user_data, comparar
            # Por ahora enviamos a todos los conductores su sede
            for s in ss:
                if s.sede_id == usuario.sede_id:
                    hora  = s.hora_inicio.strftime("%H:%M") if s.hora_inicio else "--:--"
                    ruta  = s.ruta.nombre[:40] if s.ruta else f"Ruta #{s.ruta_id}"
                    placa = s.vehiculo.placa if s.vehiculo else f"#{s.vehiculo_id}"
                    lineas.append(f"🕐 {hora} — {ruta}\n🚌 Vehículo: {placa}\n")
                    encontrado = True

        if not encontrado:
            continue

        lineas.append("✅ Recuerda llegar puntual. ¡Buenas noches!")

        try:
            await app.bot.send_message(
                chat_id=usuario.telegram_id,
                text="\n".join(lineas),
                parse_mode="Markdown",
            )
            logger.info("Notificación enviada al conductor telegram_id=%s", usuario.telegram_id)
        except Exception as e:
            logger.warning(
                "No se pudo enviar notificación al conductor %s: %s",
                usuario.telegram_id, e
            )


# ─────────────────────────────────────────────
# Job 2 — Alerta matutina a programadores
# ─────────────────────────────────────────────
async def alertar_programadores(context):
    """
    Se ejecuta cada día a las 07:00 (hora Lima).
    Avisa a programadores si hay servicios del día sin conductor asignado.
    """
    hoy = date.today()
    app: Application = context.application

    with get_session() as db:
        # Servicios sin conductor (conductor_id = 0 o nulo)
        sin_conductor = (
            db.query(Servicio)
            .options(joinedload(Servicio.ruta))
            .filter(
                Servicio.fecha  == hoy,
                Servicio.estado == "PROGRAMADO",
                Servicio.conductor_id.is_(None),
            )
            .all()
        )

        programadores = (
            db.query(Usuario)
            .filter(
                Usuario.rol.in_(["programador", "administrador"]),
                Usuario.activo == True,
                Usuario.telegram_id.isnot(None),
            )
            .all()
        )

    if not sin_conductor:
        logger.info("Alerta programadores: todos los servicios tienen conductor asignado.")
        return

    for prog in programadores:
        servicios_sede = [s for s in sin_conductor if s.sede_id == prog.sede_id]
        if not servicios_sede:
            continue

        lineas = [
            f"⚠️ *Alerta — {hoy.strftime('%d/%m/%Y')}*\n\n"
            f"Hay *{len(servicios_sede)} servicio(s)* sin conductor asignado en tu sede:\n"
        ]
        for s in servicios_sede:
            hora = s.hora_inicio.strftime("%H:%M") if s.hora_inicio else "--:--"
            ruta = s.ruta.nombre[:40] if s.ruta else f"Ruta #{s.ruta_id}"
            lineas.append(f"🕐 {hora} — {ruta} (ID: {s.servicio_id})")

        lineas.append("\nUsa /nuevo para asignar un conductor.")

        try:
            await app.bot.send_message(
                chat_id=prog.telegram_id,
                text="\n".join(lineas),
                parse_mode="Markdown",
            )
            logger.info("Alerta enviada al programador telegram_id=%s", prog.telegram_id)
        except Exception as e:
            logger.warning(
                "No se pudo enviar alerta al programador %s: %s",
                prog.telegram_id, e
            )


# ─────────────────────────────────────────────
# Registro de jobs en la aplicación
# ─────────────────────────────────────────────
def register_jobs(app: Application):
    """
    Registra los dos jobs diarios usando el JobQueue de python-telegram-bot.
    Los horarios usan la zona horaria configurada en settings (America/Lima).
    """
    import datetime
    import pytz

    tz = pytz.timezone(settings.timezone)

    # Notificación conductores — 20:00 Lima
    hora_conductores = datetime.time(
        hour=settings.hora_notif_conductores,
        minute=0,
        tzinfo=tz,
    )
    app.job_queue.run_daily(
        notificar_conductores,
        time=hora_conductores,
        name="notif_conductores",
    )

    # Alerta programadores — 07:00 Lima
    hora_programadores = datetime.time(
        hour=settings.hora_notif_programador,
        minute=0,
        tzinfo=tz,
    )
    app.job_queue.run_daily(
        alertar_programadores,
        time=hora_programadores,
        name="alerta_programadores",
    )

    logger.info(
        "Jobs registrados: notif_conductores=%s:00, alerta_programadores=%s:00 (%s)",
        settings.hora_notif_conductores,
        settings.hora_notif_programador,
        settings.timezone,
    )
