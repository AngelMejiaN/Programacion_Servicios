from pydantic import BaseModel
from typing import Optional


class ParaderoBase(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    sede_id: int
    activo: bool = True


class ParaderoCreate(ParaderoBase):
    pass


class ParaderoResponse(ParaderoBase):
    paradero_id: int
    model_config = {"from_attributes": True}
