from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base


class SedeLocal(Base):
    """
    Relación sede ↔ local (emp_local_id de T_EMPLEADOS).
    Reemplaza el campo locales VARCHAR(50) con comas que tenía PG_SEDE.
    El JOIN con T_EMPLEADOS usa: SedeLocal.local_id = T_EMPLEADOS.emp_local_id
    """
    __tablename__ = "PG_SEDE_LOCAL"
    __table_args__ = (UniqueConstraint("sede_id", "local_id", name="uq_sede_local"),)

    id       = Column(Integer, primary_key=True, autoincrement=True)
    sede_id  = Column(Integer, ForeignKey("PG_SEDE.sede_id"), nullable=False, index=True)
    local_id = Column(Integer, nullable=False)

    sede = relationship("Sede", back_populates="locales_rel")
