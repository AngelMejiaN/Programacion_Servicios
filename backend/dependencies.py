"""
dependencies.py
===============
Dependencias de autenticación para FastAPI.
Soporta dos métodos:
  1. Header X-Telegram-Id  — usado por el bot de Telegram
  2. Authorization: Bearer <JWT>  — usado por la web
"""
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from .database import get_db
from .models.usuario import Usuario
from .auth import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_usuario_activo(
    telegram_id: int | None = Header(default=None, alias="X-Telegram-Id"),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Resuelve el usuario autenticado desde cualquiera de las dos fuentes:
    - X-Telegram-Id header (bot)
    - Authorization: Bearer <token> (web)
    """
    usuario: Usuario | None = None

    # ── 1. JWT (web) ─────────────────────────────────────────────────────────
    if credentials and credentials.credentials:
        try:
            payload    = decode_token(credentials.credentials)
            usuario_id = int(payload["sub"])
            usuario    = (
                db.query(Usuario)
                .filter(Usuario.usuario_id == usuario_id, Usuario.activo == True)
                .first()
            )
        except (JWTError, KeyError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ── 2. Telegram header (bot) ─────────────────────────────────────────────
    elif telegram_id:
        usuario = (
            db.query(Usuario)
            .filter(Usuario.telegram_id == telegram_id, Usuario.activo == True)
            .first()
        )

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def require_rol(*roles: str):
    """
    Dependencia de fábrica: restringe el endpoint a ciertos roles.
    Uso: Depends(require_rol("administrador", "programador"))
    """
    def _check(usuario: Usuario = Depends(get_usuario_activo)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de estos roles: {', '.join(roles)}",
            )
        return usuario
    return _check
