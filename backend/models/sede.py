from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class Sede(Base):
    __tablename__ = "PG_SEDE"

    sede_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre  = Column(String(100), nullable=False)
    tipo    = Column(String(1),   nullable=False)   # A | B | C
    locales = Column(String(50),  nullable=True)    # IDs separados por coma → T_EMPLEADOS.emp_local_id
    activa  = Column(Boolean,     nullable=False, default=True)

    vehiculos  = relationship("Vehiculo",  back_populates="sede")
    paraderos  = relationship("Paradero",  back_populates="sede")
    rutas      = relationship("Ruta",      back_populates="sede")
    usuarios   = relationship("Usuario",   back_populates="sede")
    servicios  = relationship("Servicio",  back_populates="sede")
