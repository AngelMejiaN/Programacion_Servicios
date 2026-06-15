from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class RutaParadero(Base):
    __tablename__ = "PG_RUTA_PARADERO"

    ruta_id     = Column(Integer, ForeignKey("PG_RUTA.ruta_id"),         primary_key=True)
    paradero_id = Column(Integer, ForeignKey("PG_PARADERO.paradero_id"), primary_key=True)
    orden       = Column(Integer, nullable=False, default=1)

    ruta     = relationship("Ruta",     back_populates="paraderos")
    paradero = relationship("Paradero")
