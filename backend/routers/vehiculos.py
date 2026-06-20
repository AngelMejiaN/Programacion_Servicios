from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.vehiculo import Vehiculo
from ..schemas.vehiculo import VehiculoResponse, VehiculoCreate
from ..dependencies import get_usuario_activo

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"],
                   dependencies=[Depends(get_usuario_activo)])


@router.get("/", response_model=list[VehiculoResponse])
def listar_vehiculos(
    sede_id: Optional[int] = None,
    operativo: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Vehiculo)
    if sede_id is not None:
        q = q.filter(Vehiculo.sede_id == sede_id)
    if operativo is not None:
        q = q.filter(Vehiculo.operativo == operativo)
    return q.order_by(Vehiculo.placa).all()


@router.get("/{vehiculo_id}", response_model=VehiculoResponse)
def obtener_vehiculo(vehiculo_id: int, db: Session = Depends(get_db)):
    v = db.query(Vehiculo).filter(Vehiculo.vehiculo_id == vehiculo_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return v
