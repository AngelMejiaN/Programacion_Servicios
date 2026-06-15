"""
routers/auth.py
===============
POST /auth/login  →  devuelve JWT para uso en la web
POST /auth/logout →  (stateless, solo informativo)
GET  /auth/me     →  devuelve datos del usuario autenticado
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.usuario import Usuario
from ..auth import verify_password, create_access_token
from ..dependencies import get_usuario_activo

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ── Schemas ──────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    usuario_id:   int
    nombre:       str
    rol:          str
    sede_id:      int | None


class UsuarioMe(BaseModel):
    usuario_id: int
    nombre:     str
    email:      str | None
    rol:        str
    sede_id:    int | None
    activo:     bool
    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == data.email.lower().strip(), Usuario.activo == True)
        .first()
    )
    if not usuario or not usuario.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    if not verify_password(data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = create_access_token(usuario.usuario_id, usuario.rol, usuario.sede_id)
    return TokenResponse(
        access_token=token,
        usuario_id=usuario.usuario_id,
        nombre=usuario.nombre,
        rol=usuario.rol,
        sede_id=usuario.sede_id,
    )


@router.get("/me", response_model=UsuarioMe)
def me(usuario: Usuario = Depends(get_usuario_activo)):
    return usuario


@router.post("/logout")
def logout():
    # JWT es stateless; el cliente simplemente descarta el token.
    return {"ok": True, "mensaje": "Sesión cerrada"}
