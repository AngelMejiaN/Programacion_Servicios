from pydantic import BaseModel
from typing import Optional


class VehiculoBase(BaseModel):
    placa: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    color: Optional[str] = None
    sede_id: Optional[int] = None
    operativo: bool = True


class VehiculoCreate(VehiculoBase):
    pass


class VehiculoUpdate(BaseModel):
    placa:      Optional[str]  = None
    marca:      Optional[str]  = None
    modelo:     Optional[str]  = None
    anio:       Optional[int]  = None
    tipo:       Optional[str]  = None
    categoria:  Optional[str]  = None
    color:      Optional[str]  = None
    operativo:  Optional[bool] = None


class VehiculoResponse(VehiculoBase):
    vehiculo_id: int
    model_config = {"from_attributes": True}
