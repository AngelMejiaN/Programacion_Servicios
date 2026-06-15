from pydantic import BaseModel
from typing import Optional


class ClienteBase(BaseModel):
    nombre: str
    ruc: Optional[str] = None
    activo: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteResponse(ClienteBase):
    cliente_id: int
    model_config = {"from_attributes": True}
