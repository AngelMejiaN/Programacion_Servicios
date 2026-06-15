from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.sede import Sede
from ..schemas.sede import SedeResponse, SedeCreate, SedeUpdate
from ..dependencies import require_rol

router = APIRouter(prefix="/sedes", tags=["Sedes"])


@router.get("/", response_model=list[SedeResponse])
def listar_sedes(solo_activas: bool = True, db: Session = Depends(get_db)):
    q = db.query(Sede)
    if solo_activas:
        q = q.filter(Sede.activa == True)
    return q.order_by(Sede.nombre).all()


@router.get("/{sede_id}", response_model=SedeResponse)
def obtener_sede(sede_id: int, db: Session = Depends(get_db)):
    sede = db.query(Sede).filter(Sede.sede_id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return sede


@router.post("/", response_model=SedeResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_rol("administrador"))])
def crear_sede(data: SedeCreate, db: Session = Depends(get_db)):
    sede = Sede(**data.model_dump())
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return sede


@router.patch("/{sede_id}", response_model=SedeResponse,
              dependencies=[Depends(require_rol("administrador"))])
def actualizar_sede(sede_id: int, data: SedeUpdate, db: Session = Depends(get_db)):
    sede = db.query(Sede).filter(Sede.sede_id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(sede, campo, valor)
    db.commit()
    db.refresh(sede)
    return sede
