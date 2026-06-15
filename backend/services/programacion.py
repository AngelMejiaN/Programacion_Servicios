from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.ruta import Ruta
from ..models.ruta_paradero import RutaParadero
from ..schemas.servicio import ServicioCreate


def calcular_hora_llegada(hora_inicio: time, tiempo_min: int) -> tuple[time, bool]:
    """
    Calcula la hora estimada de llegada sumando tiempo_min a hora_inicio.
    Devuelve (hora_llegada, cruza_medianoche).
    """
    dt = datetime.combine(datetime.today(), hora_inicio)
    dt_llegada = dt + timedelta(minutes=tiempo_min)
    cruza_medianoche = dt_llegada.date() > dt.date()
    return dt_llegada.time(), cruza_medianoche


def validar_y_enriquecer(
    data: ServicioCreate,
    ruta: Ruta,
    db: Session,
) -> dict:
    """
    Valida las reglas de negocio según el tipo de sede (A/B/C)
    y el tipo de servicio (PERSONAL/MINAS).
    Retorna un dict con campos adicionales calculados (ej: hora_llegada_est).
    Lanza HTTPException si algo falla.
    """
    extras: dict = {}
    tipo_sede = ruta.sede.tipo  # A | B | C

    # ── Tipo A — ruta fija con hora de llegada calculada ─────────────────────
    if tipo_sede == "A":
        if ruta.calcula_llegada and ruta.tiempo_estimado_min:
            hora_est, cruza = calcular_hora_llegada(
                data.hora_inicio, ruta.tiempo_estimado_min
            )
            extras["hora_llegada_est"] = hora_est
            if cruza:
                extras["fecha_llegada"] = data.fecha + timedelta(days=1)

    # ── Tipo B — rutas fijas o variables ─────────────────────────────────────
    elif tipo_sede == "B":
        if not ruta.origen_fijo:
            # Ruta variable: exige paradero de origen
            if not data.paradero_origen_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Esta ruta variable requiere seleccionar un paradero de origen.",
                )
            # Verificar que el paradero pertenezca a esta ruta
            existe = (
                db.query(RutaParadero)
                .filter(
                    RutaParadero.ruta_id    == ruta.ruta_id,
                    RutaParadero.paradero_id == data.paradero_origen_id,
                )
                .first()
            )
            if not existe:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"El paradero {data.paradero_origen_id} no pertenece a la ruta '{ruta.nombre}'.",
                )

    # ── Tipo C — combinación paradero origen/destino ya definida en PG_RUTA ──
    # La validación es implícita: al seleccionar ruta_id se elige la combinación.
    # No se requiere lógica adicional aquí.

    # ── Rutas de mina: exige segundo conductor si es bus ─────────────────────
    if ruta.requiere_dos_conductores and not data.conductor2_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Esta ruta requiere dos conductores (conductor2_id es obligatorio).",
        )

    return extras


def calcular_hora_retorno(
    hora_salida_planta: time,
    tiempo_min: int | None,
    fecha_salida_planta: date,
) -> tuple[time | None, date | None]:
    """
    Calcula hora_retorno_est y fecha_retorno si se conoce el tiempo estimado.
    Usado en rutas Tipo A donde el retorno también se puede calcular.
    """
    if not tiempo_min:
        return None, None
    dt = datetime.combine(fecha_salida_planta, hora_salida_planta)
    dt_retorno = dt + timedelta(minutes=tiempo_min)
    cruza = dt_retorno.date() > fecha_salida_planta
    fecha_ret = dt_retorno.date() if cruza else None
    return dt_retorno.time(), fecha_ret
