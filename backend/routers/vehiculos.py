from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.vehiculo import Vehiculo
from ..schemas.vehiculo import VehiculoResponse, VehiculoCreate, VehiculoUpdate
from ..dependencies import get_usuario_activo, require_rol

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


@router.post("/", response_model=VehiculoResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_rol("administrador"))])
def crear_vehiculo(data: VehiculoCreate, db: Session = Depends(get_db)):
    v = Vehiculo(**data.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.patch("/{vehiculo_id}", response_model=VehiculoResponse,
              dependencies=[Depends(require_rol("administrador"))])
def actualizar_vehiculo(vehiculo_id: int, data: VehiculoUpdate, db: Session = Depends(get_db)):
    v = db.query(Vehiculo).filter(Vehiculo.vehiculo_id == vehiculo_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(v, campo, valor)
    db.commit()
    db.refresh(v)
    return v
