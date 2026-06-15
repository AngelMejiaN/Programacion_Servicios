from pydantic import BaseModel
from typing import Optional


class ConductorResponse(BaseModel):
    emp_id: int
    nombre_completo: str
    licencia: Optional[str] = None
    licencia_cat: Optional[str] = None
    telefono: Optional[str] = None
    model_config = {"from_attributes": True}
