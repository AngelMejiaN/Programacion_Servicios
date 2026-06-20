from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.paradero import Paradero
from ..schemas.paradero import ParaderoResponse, ParaderoCreate
from ..dependencies import get_usuario_activo

router = APIRouter(prefix="/paraderos", tags=["Paraderos"],
                   dependencies=[Depends(get_usuario_activo)])


@router.get("/", response_model=list[ParaderoResponse])
def listar_paraderos(
    sede_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Paradero).filter(Paradero.activo == True)
    if sede_id is not None:
        q = q.filter(Paradero.sede_id == sede_id)
    return q.order_by(Paradero.nombre).all()
