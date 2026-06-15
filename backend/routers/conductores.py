from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.conductor import ConductorResponse
from ..services.conductores import get_conductores_by_sede, get_conductor_by_id

router = APIRouter(prefix="/conductores", tags=["Conductores"])


@router.get("/", response_model=list[ConductorResponse])
def listar_conductores(sede_id: int, db: Session = Depends(get_db)):
    """
    Devuelve los conductores activos de una sede.
    Consulta T_EMPLEADOS filtrando por emp_carg_id=3 y los
    loc_ids configurados en PG_SEDE.locales.
    """
    conductores = get_conductores_by_sede(sede_id, db)
    return conductores


@router.get("/{emp_id}", response_model=ConductorResponse)
def obtener_conductor(emp_id: int, db: Session = Depends(get_db)):
    conductor = get_conductor_by_id(emp_id, db)
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado o inactivo")
    return conductor
