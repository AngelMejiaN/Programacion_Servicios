from pydantic import BaseModel
from typing import Optional
from .paradero import ParaderoResponse


class RutaResumen(BaseModel):
    """Schema ligero para listas desplegables en formularios."""
    ruta_id:                  int
    nombre:                   str
    cliente_id:               int
    origen_fijo:              bool
    calcula_llegada:          bool
    requiere_dos_conductores: bool
    tipo_servicio:            str
    tiempo_estimado_min:      Optional[int] = None
    model_config = {"from_attributes": True}


class RutaResponse(RutaResumen):
    sede_id: int
    cliente_id: int
    origen_texto: Optional[str] = None
    paradero_origen_id: Optional[int] = None
    destino_texto: Optional[str] = None
    paradero_destino_id: Optional[int] = None
    activa: bool
    paraderos_disponibles: list[ParaderoResponse] = []
    model_config = {"from_attributes": True}
