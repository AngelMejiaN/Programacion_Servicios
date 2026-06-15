from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class Cliente(Base):
    __tablename__ = "PG_CLIENTE"

    cliente_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre     = Column(String(100), nullable=False)
    ruc        = Column(String(20),  nullable=True)
    activo     = Column(Boolean,     nullable=False, default=True)

    rutas = relationship("Ruta", back_populates="cliente")
