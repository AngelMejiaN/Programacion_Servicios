from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.usuario import Usuario
from ..schemas.usuario import UsuarioResponse, UsuarioCreate, UsuarioUpdate
from ..dependencies import require_rol
from ..auth import hash_password

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_por_telegram(
    telegram_id: int,
    db: Session = Depends(get_db),
):
    """
    Usado por el bot de Telegram para identificar al usuario
    y conocer su rol y sede antes de iniciar cualquier flujo.
    """
    usuario = (
        db.query(Usuario)
        .filter(Usuario.telegram_id == telegram_id, Usuario.activo == True)
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no registrado en el sistema")
    return usuario


@router.get("/", response_model=list[UsuarioResponse],
            dependencies=[Depends(require_rol("administrador"))])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(Usuario.nombre).all()


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_rol("administrador"))])
def crear_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    # Verificar email duplicado
    if data.email:
        existe_email = db.query(Usuario).filter(Usuario.email == data.email.lower().strip()).first()
        if existe_email:
            raise HTTPException(status_code=400, detail=f"Ya existe un usuario con el email {data.email}")

    # Verificar telegram_id duplicado
    if data.telegram_id:
        existe_tg = db.query(Usuario).filter(Usuario.telegram_id == data.telegram_id).first()
        if existe_tg:
            raise HTTPException(status_code=400, detail=f"Ya existe un usuario con telegram_id {data.telegram_id}")

    # Construir el usuario hasheando la contraseña
    datos = data.model_dump(exclude={"password"})
    if data.email:
        datos["email"] = data.email.lower().strip()
    datos["password_hash"] = hash_password(data.password)

    usuario = Usuario(**datos)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}",
              response_model=UsuarioResponse,
              dependencies=[Depends(require_rol("administrador"))])
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        if campo == "password" and valor:
            setattr(usuario, "password_hash", hash_password(valor))
        else:
            setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}/estado",
              dependencies=[Depends(require_rol("administrador"))])
def cambiar_estado_usuario(
    usuario_id: int,
    activo: bool,
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.usuario_id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = activo
    db.commit()
    return {"ok": True, "usuario_id": usuario_id, "activo": activo}
