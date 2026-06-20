from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class ConductorDemo(Base):
    """
    Tabla de conductores solo para modo demo (SQLite).
    En producción los conductores vienen de T_EMPLEADOS (tabla externa de RRHH).
    emp_id reproduce el emp_id real para que el resto del código funcione igual.
    """
    __tablename__ = "PG_CONDUCTOR_DEMO"

    emp_id           = Column(Integer, primary_key=True)
    nombre_completo  = Column(String(150), nullable=False)
    emp_licencia     = Column(String(20),  nullable=True)
    emp_licencia_cat = Column(String(10),  nullable=True)
    emp_telefono     = Column(String(20),  nullable=True)
    sede_id          = Column(Integer, ForeignKey("PG_SEDE.sede_id"), nullable=False)
    activo           = Column(Boolean, nullable=False, default=True)

    sede = relationship("Sede")
