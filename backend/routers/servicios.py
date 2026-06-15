from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from datetime import date
from typing import Optional

from ..database import get_db
from ..models.servicio import Servicio
from ..models.ruta import Ruta
from ..models.vehiculo import Vehiculo
from ..models.cliente import Cliente
from ..schemas.servicio import (
    ServicioCreate, ServicioResponse, ServicioUpdate,
    EstadoUpdate, LlegadaUpdate, RetornoUpdate, RetornoRealUpdate,
)
from ..dependencies import get_usuario_activo, require_rol
from ..models.usuario import Usuario
from ..services.programacion import validar_y_enriquecer, calcular_hora_retorno
from ..services.importacion import generar_plantilla, importar_desde_excel

router = APIRouter(prefix="/servicios", tags=["Servicios"])


# ─────────────────────────────────────────────
# GET /servicios/  — programación del día/semana
# ─────────────────────────────────────────────
@router.get("/", response_model=list[ServicioResponse])
def listar_servicios(
    sede_id: int,
    fecha: date = Query(default_factory=date.today),
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Devuelve los servicios de una sede para una fecha dada.
    Acepta filtro opcional por estado.
    """
    q = (
        db.query(Servicio)
        .options(
            joinedload(Servicio.ruta).joinedload(Ruta.cliente),
            joinedload(Servicio.vehiculo),
            joinedload(Servicio.paradero_origen),
            joinedload(Servicio.sede),
        )
        .filter(Servicio.sede_id == sede_id, Servicio.fecha == fecha)
    )
    if estado:
        q = q.filter(Servicio.estado == estado.upper())
    return q.order_by(Servicio.hora_inicio).all()


# ─────────────────────────────────────────────
# GET /servicios/plantilla  — DEBE ir antes de /{servicio_id}
# ─────────────────────────────────────────────
@router.get("/plantilla")
def descargar_plantilla(
    sede_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    archivo_bytes = generar_plantilla(sede_id, db)
    filename = f"plantilla_servicios_sede{sede_id}.xlsx"
    return Response(
        content=archivo_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─────────────────────────────────────────────
# POST /servicios/importar  — DEBE ir antes de /{servicio_id}
# ─────────────────────────────────────────────
@router.post("/importar")
def importar_servicios(
    sede_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    if not archivo.filename or not archivo.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo debe ser un .xlsx generado con la plantilla oficial.",
        )
    resultado = importar_desde_excel(
        archivo=archivo.file,
        sede_id=sede_id,
        usuario_id=usuario.usuario_id,
        db=db,
    )
    if not resultado.get("ok", True) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return resultado


@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    s = db.query(Servicio).filter(Servicio.servicio_id == servicio_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return s


# ─────────────────────────────────────────────
# POST /servicios/  — crear nuevo servicio
# ─────────────────────────────────────────────
@router.post("/", response_model=ServicioResponse, status_code=status.HTTP_201_CREATED)
def crear_servicio(
    data: ServicioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    # 1. Cargar ruta con relaciones necesarias para validación
    ruta = (
        db.query(Ruta)
        .options(joinedload(Ruta.sede))
        .filter(Ruta.ruta_id == data.ruta_id, Ruta.activa == True)
        .first()
    )
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada o inactiva")

    # Validar que el servicio pertenece a la sede del usuario (salvo admin)
    if usuario.rol != "administrador" and data.sede_id != usuario.sede_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear servicios para otra sede",
        )

    # 2. Verificar vehículo operativo
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.vehiculo_id == data.vehiculo_id,
        Vehiculo.operativo == True,
    ).first()
    if not vehiculo:
        raise HTTPException(status_code=400, detail="El vehículo no está operativo")

    # 3. Validaciones de negocio (A/B/C) y enriquecimiento de campos
    extras = validar_y_enriquecer(data, ruta, db)

    # 4. Crear el servicio
    servicio_data = data.model_dump()
    servicio_data.update(extras)
    servicio_data["creado_por"] = usuario.usuario_id
    servicio_data["estado"] = "PROGRAMADO"

    servicio = Servicio(**servicio_data)
    db.add(servicio)
    db.commit()
    db.refresh(servicio)
    return servicio


# ─────────────────────────────────────────────
# PATCH /servicios/{id}  — editar campos básicos
# ─────────────────────────────────────────────
@router.patch("/{servicio_id}", response_model=ServicioResponse)
def actualizar_servicio(
    servicio_id: int,
    data: ServicioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    s = _get_servicio_editable(servicio_id, usuario, db)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(s, campo, valor)
    db.commit()
    db.refresh(s)
    return s


# ─────────────────────────────────────────────
# PATCH /servicios/{id}/estado
# ─────────────────────────────────────────────
@router.patch("/{servicio_id}/estado", response_model=ServicioResponse)
def cambiar_estado(
    servicio_id: int,
    data: EstadoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    s = _get_servicio_editable(servicio_id, usuario, db)

    # Validar transiciones permitidas
    transiciones = {
        "PROGRAMADO": ["EN_CURSO", "CANCELADO"],
        "EN_CURSO":   ["COMPLETADO", "CANCELADO"],
        "COMPLETADO": [],
        "CANCELADO":  [],
    }
    if data.estado not in transiciones.get(s.estado, []):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cambiar de '{s.estado}' a '{data.estado}'",
        )
    s.estado = data.estado
    if data.observaciones:
        s.observaciones = data.observaciones
    db.commit()
    db.refresh(s)
    return s


# ─────────────────────────────────────────────
# PATCH /servicios/{id}/llegada — hora llegada real
# ─────────────────────────────────────────────
@router.patch("/{servicio_id}/llegada", response_model=ServicioResponse)
def registrar_llegada(
    servicio_id: int,
    data: LlegadaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    s = _get_servicio_editable(servicio_id, usuario, db)
    s.hora_llegada_real = data.hora_llegada_real
    if data.fecha_llegada:
        s.fecha_llegada = data.fecha_llegada
    db.commit()
    db.refresh(s)
    return s


# ─────────────────────────────────────────────
# PATCH /servicios/{id}/retorno — programar retorno
# ─────────────────────────────────────────────
@router.patch("/{servicio_id}/retorno", response_model=ServicioResponse)
def registrar_retorno(
    servicio_id: int,
    data: RetornoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    s = _get_servicio_editable(servicio_id, usuario, db)

    # Calcular hora_retorno_est si la ruta lo permite (Tipo A)
    ruta = db.query(Ruta).filter(Ruta.ruta_id == s.ruta_id).first()
    fecha_base = data.fecha_retorno or s.fecha
    hora_est, fecha_ret = calcular_hora_retorno(
        data.hora_salida_planta,
        ruta.tiempo_estimado_min if ruta and ruta.calcula_llegada else None,
        fecha_base,
    )

    s.retorno_misma_unidad  = data.retorno_misma_unidad
    s.retorno_vehiculo_id   = data.retorno_vehiculo_id
    s.retorno_conductor_id  = data.retorno_conductor_id
    s.retorno_conductor2_id = data.retorno_conductor2_id
    s.hora_salida_planta    = data.hora_salida_planta
    s.hora_retorno_est      = data.hora_retorno_est or hora_est
    s.fecha_retorno         = data.fecha_retorno or fecha_ret

    db.commit()
    db.refresh(s)
    return s


# ─────────────────────────────────────────────
# PATCH /servicios/{id}/retorno/real — llegada real del retorno
# ─────────────────────────────────────────────
@router.patch("/{servicio_id}/retorno/real", response_model=ServicioResponse)
def registrar_retorno_real(
    servicio_id: int,
    data: RetornoRealUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    s = _get_servicio_editable(servicio_id, usuario, db)
    s.hora_retorno_real = data.hora_retorno_real
    db.commit()
    db.refresh(s)
    return s


# ─────────────────────────────────────────────
# DELETE /servicios/{id}  — cancelar servicio
# ─────────────────────────────────────────────
@router.delete("/{servicio_id}", status_code=status.HTTP_200_OK)
def cancelar_servicio(
    servicio_id: int,
    motivo: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_rol("administrador", "programador")),
):
    s = _get_servicio_editable(servicio_id, usuario, db)
    if s.estado == "COMPLETADO":
        raise HTTPException(status_code=400, detail="No se puede cancelar un servicio completado")
    s.estado = "CANCELADO"
    if motivo:
        s.observaciones = motivo
    db.commit()
    return {"ok": True, "servicio_id": servicio_id, "estado": "CANCELADO"}


# ─────────────────────────────────────────────
# Helper interno
# ─────────────────────────────────────────────
def _get_servicio_editable(
    servicio_id: int,
    usuario: Usuario,
    db: Session,
) -> Servicio:
    """
    Obtiene un servicio y valida que el usuario tenga permiso de editarlo.
    Lanza 404 si no existe o 403 si pertenece a otra sede.
    """
    s = db.query(Servicio).filter(Servicio.servicio_id == servicio_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    if usuario.rol != "administrador" and s.sede_id != usuario.sede_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar servicios de otra sede",
        )
    return s
