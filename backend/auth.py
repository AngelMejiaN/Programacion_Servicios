"""
auth.py
=======
Utilidades JWT y hashing de contraseñas para autenticación web.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from .config import settings

# ── Configuración ────────────────────────────────────────────────────────────
SECRET_KEY  = getattr(settings, "secret_key",  "cambiar-en-produccion-32-chars-min")
ALGORITHM   = "HS256"
TOKEN_HOURS = 8     # Duración del token (jornada laboral)


# ── Contraseñas ──────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ──────────────────────────────────────────────────────────────────────
def create_access_token(usuario_id: int, rol: str, sede_id: int | None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    payload = {
        "sub":     str(usuario_id),
        "rol":     rol,
        "sede_id": sede_id,
        "exp":     expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica y valida el token. Lanza JWTError si es inválido/expirado."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
