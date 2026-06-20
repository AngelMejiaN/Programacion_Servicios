from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.cliente import Cliente
from ..schemas.cliente import ClienteResponse, ClienteCreate
from ..dependencies import get_usuario_activo

router = APIRouter(prefix="/clientes", tags=["Clientes"],
                   dependencies=[Depends(get_usuario_activo)])


@router.get("/", response_model=list[ClienteResponse])
def listar_clientes(
    activos: bool = True,
    sede_id: int | None = None,
    db: Session = Depends(get_db)
):
    """Lista clientes. Con sede_id devuelve solo los que tienen rutas en esa sede."""
    if sede_id:
        from ..models.ruta import Ruta
        cliente_ids = (
            db.query(Ruta.cliente_id)
            .filter(Ruta.sede_id == sede_id, Ruta.activa == True)
            .distinct()
            .all()
        )
        ids = [c[0] for c in cliente_ids if c[0]]
        q = db.query(Cliente).filter(Cliente.cliente_id.in_(ids))
    else:
        q = db.query(Cliente)
    if activos:
        q = q.filter(Cliente.activo == True)
    return q.order_by(Cliente.nombre).all()


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.cliente_id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente
