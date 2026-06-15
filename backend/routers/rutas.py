from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from ..database import get_db
from ..models.ruta import Ruta
from ..models.ruta_paradero import RutaParadero
from ..models.paradero import Paradero
from ..schemas.ruta import RutaResponse, RutaResumen
from ..schemas.paradero import ParaderoResponse

router = APIRouter(prefix="/rutas", tags=["Rutas"])


@router.get("/", response_model=list[RutaResumen])
def listar_rutas(
    sede_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    tipo_servicio: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Lista rutas activas. Acepta filtros por sede, cliente y tipo de servicio.
    Este endpoint alimenta el selector de rutas en el formulario.
    """
    q = db.query(Ruta).filter(Ruta.activa == True)
    if sede_id is not None:
        q = q.filter(Ruta.sede_id == sede_id)
    if cliente_id is not None:
        q = q.filter(Ruta.cliente_id == cliente_id)
    if tipo_servicio is not None:
        q = q.filter(Ruta.tipo_servicio == tipo_servicio.upper())
    return q.order_by(Ruta.nombre).all()


@router.get("/{ruta_id}", response_model=RutaResponse)
def obtener_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """
    Detalle completo de una ruta, incluyendo los paraderos disponibles
    si es una ruta variable (Tipo B con origen_fijo=False).
    """
    ruta = (
        db.query(Ruta)
        .options(
            joinedload(Ruta.paraderos).joinedload(RutaParadero.paradero),
            joinedload(Ruta.paradero_origen),
            joinedload(Ruta.paradero_destino),
        )
        .filter(Ruta.ruta_id == ruta_id)
        .first()
    )
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")

    # Construir lista de paraderos disponibles (solo rutas variables Tipo B)
    paraderos_disponibles = []
    if not ruta.origen_fijo:
        paraderos_disponibles = [
            ParaderoResponse.model_validate(rp.paradero)
            for rp in sorted(ruta.paraderos, key=lambda x: x.orden)
        ]

    response = RutaResponse.model_validate(ruta)
    response.paraderos_disponibles = paraderos_disponibles
    return response


@router.get("/{ruta_id}/paraderos", response_model=list[ParaderoResponse])
def paraderos_de_ruta(ruta_id: int, db: Session = Depends(get_db)):
    """
    Devuelve los paraderos de origen disponibles para una ruta variable (Tipo B).
    Ordenados por el campo 'orden' de PG_RUTA_PARADERO.
    """
    ruta = db.query(Ruta).filter(Ruta.ruta_id == ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    if ruta.origen_fijo:
        raise HTTPException(
            status_code=400,
            detail="Esta ruta tiene origen fijo, no tiene lista de paraderos seleccionables.",
        )
    paraderos = (
        db.query(Paradero)
        .join(RutaParadero, RutaParadero.paradero_id == Paradero.paradero_id)
        .filter(RutaParadero.ruta_id == ruta_id, Paradero.activo == True)
        .order_by(RutaParadero.orden)
        .all()
    )
    return paraderos
