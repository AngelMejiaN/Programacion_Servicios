from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TipoProgramacion(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class SedeBase(BaseModel):
    nombre: str
    tipo: TipoProgramacion
    locales: Optional[str] = None
    activa: bool = True


class SedeCreate(SedeBase):
    pass


class SedeUpdate(BaseModel):
    nombre: Optional[str] = None
    locales: Optional[str] = None
    activa: Optional[bool] = None


class SedeResponse(SedeBase):
    sede_id: int
    model_config = {"from_attributes": True}
