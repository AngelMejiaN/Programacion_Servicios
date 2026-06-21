from pydantic import BaseModel
from typing import Optional


class ConductorCreate(BaseModel):
    nombre_completo: str
    licencia:        Optional[str] = None
    licencia_cat:    Optional[str] = None
    telefono:        Optional[str] = None
    sede_id:         int


class ConductorUpdate(BaseModel):
    nombre_completo: Optional[str]  = None
    licencia:        Optional[str]  = None
    licencia_cat:    Optional[str]  = None
    telefono:        Optional[str]  = None
    activo:          Optional[bool] = None


class ConductorResponse(BaseModel):
    emp_id:          int
    nombre_completo: str
    licencia:        Optional[str]  = None
    licencia_cat:    Optional[str]  = None
    telefono:        Optional[str]  = None
    activo:          bool            = True
    model_config = {"from_attributes": True}
