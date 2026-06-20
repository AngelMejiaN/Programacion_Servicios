from sqlalchemy import Column, Integer, String, Boolean, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Usuario(Base):
    __tablename__ = "PG_USUARIO"

    usuario_id    = Column(Integer,    primary_key=True, autoincrement=True)
    nombre        = Column(String(100), nullable=False)
    email         = Column(String(150), nullable=True, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)   # NULL para usuarios solo-bot
    telegram_id   = Column(BigInteger,  nullable=True, index=True)
    # emp_id vincula usuarios-conductor con T_EMPLEADOS / PG_CONDUCTOR_DEMO.
    # Permite que el bot mapee conductor_id del servicio al telegram_id correcto.
    emp_id        = Column(Integer,     nullable=True, index=True)
    rol           = Column(String(20),  nullable=False)
    # roles válidos: administrador | programador | supervisor | conductor
    sede_id       = Column(Integer, ForeignKey("PG_SEDE.sede_id"), nullable=True)
    activo        = Column(Boolean,     nullable=False, default=True)

    sede = relationship("Sede", back_populates="usuarios")
