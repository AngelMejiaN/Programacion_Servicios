"""
Conexión a SQL Server — misma lógica que backend/database.py,
pero independiente para que el bot pueda correr sin el backend.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_session():
    """
    Context manager para handlers del bot.
    expunge_all() desvincula los objetos ORM de la sesión antes de cerrarla,
    preservando los atributos ya cargados para usarlos fuera del bloque 'with'.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.expunge_all()
        session.close()
