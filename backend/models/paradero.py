from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Paradero(Base):
    __tablename__ = "PG_PARADERO"

    paradero_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(150), nullable=False)
    direccion   = Column(String(200), nullable=True)
    sede_id     = Column(Integer, ForeignKey("PG_SEDE.sede_id"), nullable=False)
    activo      = Column(Boolean, nullable=False, default=True)

    sede = relationship("Sede", back_populates="paraderos")
