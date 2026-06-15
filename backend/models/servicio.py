from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Time, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Servicio(Base):
    __tablename__ = "PG_SERVICIO"

    servicio_id        = Column(Integer, primary_key=True, autoincrement=True)
    fecha              = Column(Date,    nullable=False, index=True)
    ruta_id            = Column(Integer, ForeignKey("PG_RUTA.ruta_id"),      nullable=False)
    sede_id            = Column(Integer, ForeignKey("PG_SEDE.sede_id"),      nullable=False, index=True)
    vehiculo_id        = Column(Integer, ForeignKey("PG_VEHICULO.vehiculo_id"), nullable=False)
    conductor_id       = Column(Integer, nullable=False)   # T_EMPLEADOS.emp_id
    conductor2_id      = Column(Integer, nullable=True)    # segundo conductor (rutas mina/bus)
    paradero_origen_id = Column(Integer, ForeignKey("PG_PARADERO.paradero_id"), nullable=True)

    hora_inicio       = Column(Time, nullable=True)
    hora_llegada_est  = Column(Time, nullable=True)
    hora_llegada_real = Column(Time, nullable=True)
    fecha_llegada     = Column(Date, nullable=True)   # distinto a fecha si cruza medianoche
    hora_fin_manual   = Column(Time, nullable=True)   # Tipo B: hora fin ingresada manualmente

    estado        = Column(String(15), nullable=False, default="PROGRAMADO")
    observaciones = Column(Text,       nullable=True)
    creado_por    = Column(Integer, ForeignKey("PG_USUARIO.usuario_id"), nullable=True)
    fecha_creacion= Column(DateTime, nullable=False, server_default=func.now())

    # Retorno
    fecha_retorno        = Column(Date,    nullable=True)  # NULL = mismo día
    retorno_misma_unidad = Column(Boolean, nullable=False, default=True)
    retorno_vehiculo_id  = Column(Integer, ForeignKey("PG_VEHICULO.vehiculo_id"), nullable=True)
    retorno_conductor_id = Column(Integer, nullable=True)   # T_EMPLEADOS.emp_id
    retorno_conductor2_id= Column(Integer, nullable=True)   # segundo conductor retorno
    hora_salida_planta   = Column(Time, nullable=True)
    hora_retorno_est     = Column(Time, nullable=True)
    hora_retorno_real    = Column(Time, nullable=True)

    # Relaciones
    ruta            = relationship("Ruta",     back_populates="servicios")
    sede            = relationship("Sede",     back_populates="servicios")
    vehiculo        = relationship("Vehiculo", foreign_keys=[vehiculo_id])
    retorno_vehiculo= relationship("Vehiculo", foreign_keys=[retorno_vehiculo_id])
    paradero_origen = relationship("Paradero")
    creador         = relationship("Usuario")

    # Propiedades calculadas — leídas por ServicioResponse (Pydantic from_attributes)
    @property
    def ruta_nombre(self) -> str | None:
        try: return self.ruta.nombre if self.ruta else None
        except Exception: return None

    @property
    def cliente_nombre(self) -> str | None:
        try: return self.ruta.cliente.nombre if (self.ruta and self.ruta.cliente) else None
        except Exception: return None

    @property
    def vehiculo_placa(self) -> str | None:
        try: return self.vehiculo.placa if self.vehiculo else None
        except Exception: return None

    @property
    def paradero_origen_nombre(self) -> str | None:
        try: return self.paradero_origen.nombre if self.paradero_origen else None
        except Exception: return None

    @property
    def sede_nombre(self) -> str | None:
        try: return self.sede.nombre if self.sede else None
        except Exception: return None
