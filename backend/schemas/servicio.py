from pydantic import BaseModel, model_validator
from datetime import date, time, datetime
from typing import Optional
from enum import Enum


class EstadoServicio(str, Enum):
    PROGRAMADO = "PROGRAMADO"
    EN_CURSO   = "EN_CURSO"
    COMPLETADO = "COMPLETADO"
    CANCELADO  = "CANCELADO"


class ServicioCreate(BaseModel):
    fecha: date
    ruta_id: int
    sede_id: int
    vehiculo_id: int
    conductor_id: int
    conductor2_id: Optional[int] = None
    paradero_origen_id: Optional[int] = None
    hora_inicio: time
    hora_fin_manual: Optional[time] = None
    observaciones: Optional[str] = None
    # Retorno
    retorno_misma_unidad: bool = True
    retorno_vehiculo_id: Optional[int] = None
    retorno_conductor_id: Optional[int] = None
    retorno_conductor2_id: Optional[int] = None
    hora_salida_planta: Optional[time] = None

    @model_validator(mode="after")
    def validar_retorno(self) -> "ServicioCreate":
        if not self.retorno_misma_unidad:
            if not self.retorno_vehiculo_id:
                raise ValueError("Si el retorno es con otra unidad, se requiere retorno_vehiculo_id")
            if not self.retorno_conductor_id:
                raise ValueError("Si el retorno es con otra unidad, se requiere retorno_conductor_id")
        return self


class ServicioUpdate(BaseModel):
    """Para PATCH /servicios/{id} — campos parciales."""
    vehiculo_id: Optional[int] = None
    conductor_id: Optional[int] = None
    conductor2_id: Optional[int] = None
    hora_inicio: Optional[time] = None
    observaciones: Optional[str] = None


class EstadoUpdate(BaseModel):
    estado: EstadoServicio
    observaciones: Optional[str] = None


class LlegadaUpdate(BaseModel):
    """Registrar llegada real al destino."""
    hora_llegada_real: time
    fecha_llegada: Optional[date] = None  # si cruzó medianoche


class RetornoUpdate(BaseModel):
    """Registrar datos del retorno."""
    retorno_misma_unidad: bool = True
    retorno_vehiculo_id: Optional[int] = None
    retorno_conductor_id: Optional[int] = None
    retorno_conductor2_id: Optional[int] = None
    hora_salida_planta: time
    hora_retorno_est: Optional[time] = None
    fecha_retorno: Optional[date] = None  # si retorno es otro día


class RetornoRealUpdate(BaseModel):
    """Registrar llegada real del retorno."""
    hora_retorno_real: time


class ServicioResponse(BaseModel):
    servicio_id: int
    fecha: date
    ruta_id: int
    sede_id: int
    vehiculo_id: int
    conductor_id: int
    conductor2_id: Optional[int] = None
    paradero_origen_id: Optional[int] = None
    hora_inicio: Optional[time] = None
    hora_llegada_est: Optional[time] = None
    hora_llegada_real: Optional[time] = None
    fecha_llegada: Optional[date] = None
    hora_fin_manual: Optional[time] = None
    estado: EstadoServicio
    observaciones: Optional[str] = None
    creado_por: Optional[int] = None
    fecha_creacion: datetime
    # Campos enriquecidos (desde relaciones ORM)
    ruta_nombre:             Optional[str] = None
    cliente_nombre:          Optional[str] = None
    vehiculo_placa:          Optional[str] = None
    paradero_origen_nombre:  Optional[str] = None
    sede_nombre:             Optional[str] = None
    # Retorno
    fecha_retorno: Optional[date] = None
    retorno_misma_unidad: bool
    retorno_vehiculo_id: Optional[int] = None
    retorno_conductor_id: Optional[int] = None
    retorno_conductor2_id: Optional[int] = None
    hora_salida_planta: Optional[time] = None
    hora_retorno_est: Optional[time] = None
    hora_retorno_real: Optional[time] = None
    model_config = {"from_attributes": True}
