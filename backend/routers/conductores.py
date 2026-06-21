from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.conductor import ConductorCreate, ConductorUpdate, ConductorResponse
from ..services.conductores import (
    get_conductores_by_sede, get_conductor_by_id,
    create_conductor, update_conductor,
)
from ..dependencies import get_usuario_activo, require_rol
from ..config import settings

router = APIRouter(prefix="/conductores", tags=["Conductores"],
                   dependencies=[Depends(get_usuario_activo)])


@router.get("/", response_model=list[ConductorResponse])
def listar_conductores(
    sede_id: int,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
):
    return get_conductores_by_sede(sede_id, db, incluir_inactivos)


@router.get("/{emp_id}", response_model=ConductorResponse)
def obtener_conductor(emp_id: int, db: Session = Depends(get_db)):
    conductor = get_conductor_by_id(emp_id, db)
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado o inactivo")
    return conductor


@router.post("/", response_model=ConductorResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_rol("administrador"))])
def crear_conductor(data: ConductorCreate, db: Session = Depends(get_db)):
    if not settings.demo_mode:
        raise HTTPException(status_code=501, detail="Alta de conductores no disponible en producción (gestionar desde RRHH)")
    return create_conductor(data, db)


@router.patch("/{emp_id}", response_model=ConductorResponse,
              dependencies=[Depends(require_rol("administrador"))])
def actualizar_conductor(emp_id: int, data: ConductorUpdate, db: Session = Depends(get_db)):
    if not settings.demo_mode:
        raise HTTPException(status_code=501, detail="Edición de conductores no disponible en producción (gestionar desde RRHH)")
    conductor = update_conductor(emp_id, data, db)
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return conductor
