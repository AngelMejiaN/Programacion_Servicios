from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Ruta(Base):
    __tablename__ = "PG_RUTA"

    ruta_id                  = Column(Integer, primary_key=True, autoincrement=True)
    nombre                   = Column(String(100), nullable=False)
    sede_id                  = Column(Integer, ForeignKey("PG_SEDE.sede_id"),      nullable=False)
    cliente_id               = Column(Integer, ForeignKey("PG_CLIENTE.cliente_id"), nullable=False)
    origen_fijo              = Column(Boolean, nullable=False, default=True)
    origen_texto             = Column(String(200), nullable=True)
    paradero_origen_id       = Column(Integer, ForeignKey("PG_PARADERO.paradero_id"), nullable=True)
    destino_texto            = Column(String(200), nullable=True)
    paradero_destino_id      = Column(Integer, ForeignKey("PG_PARADERO.paradero_id"), nullable=True)
    tiempo_estimado_min      = Column(Integer, nullable=True)
    calcula_llegada          = Column(Boolean, nullable=False, default=False)
    requiere_dos_conductores = Column(Boolean, nullable=False, default=False)
    tipo_servicio            = Column(String(15), nullable=False, default="PERSONAL")
    activa                   = Column(Boolean, nullable=False, default=True)

    sede            = relationship("Sede",     back_populates="rutas")
    cliente         = relationship("Cliente",  back_populates="rutas")
    paradero_origen = relationship("Paradero", foreign_keys=[paradero_origen_id])
    paradero_destino= relationship("Paradero", foreign_keys=[paradero_destino_id])
    paraderos       = relationship("RutaParadero", back_populates="ruta",
                                   order_by="RutaParadero.orden")
    servicios       = relationship("Servicio", back_populates="ruta")
