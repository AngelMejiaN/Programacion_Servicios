from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class Rol(str, Enum):
    administrador = "administrador"
    programador   = "programador"
    supervisor    = "supervisor"
    conductor     = "conductor"


class UsuarioBase(BaseModel):
    nombre:      str
    email:       Optional[str] = None
    telegram_id: Optional[int] = None
    rol:         Rol
    sede_id:     Optional[int] = None
    activo:      bool = True


class UsuarioCreate(UsuarioBase):
    password: str   # Contraseña en texto plano — se hashea en el router


class UsuarioUpdate(BaseModel):
    nombre:      Optional[str] = None
    email:       Optional[str] = None
    telegram_id: Optional[int] = None
    rol:         Optional[Rol] = None
    sede_id:     Optional[int] = None
    password:    Optional[str] = None   # Nueva contraseña (opcional)


class UsuarioResponse(UsuarioBase):
    usuario_id: int
    model_config = {"from_attributes": True}
