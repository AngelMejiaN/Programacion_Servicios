from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Vehiculo(Base):
    __tablename__ = "PG_VEHICULO"

    vehiculo_id = Column(Integer, primary_key=True, autoincrement=True)
    placa       = Column(String(10),  nullable=False)
    marca       = Column(String(50),  nullable=True)
    modelo      = Column(String(50),  nullable=True)
    anio        = Column(Integer,     nullable=True)
    tipo        = Column(String(20),  nullable=True)
    categoria   = Column(String(50),  nullable=True)
    color       = Column(String(30),  nullable=True)
    sede_id     = Column(Integer, ForeignKey("PG_SEDE.sede_id"), nullable=True)
    operativo   = Column(Boolean, nullable=False, default=True)

    sede = relationship("Sede", back_populates="vehiculos")
