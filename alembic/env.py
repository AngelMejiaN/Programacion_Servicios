"""
alembic/env.py
==============
Configuración de entorno para migraciones Alembic.
- Usa la misma URL de base de datos que settings.database_url.
- Importa todos los modelos ORM para que --autogenerate los detecte.
- No aplica migraciones en modo demo (SQLite); usa Base.metadata.create_all en startup.
"""
import sys
import os

# Añadir la raíz del proyecto al path para que los imports de backend funcionen.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# Importar settings y todos los modelos
from backend.config import settings
from backend.database import Base

# noqa: F401 — importar modelos para que Base los registre
from backend.models import (  # noqa: F401
    Sede, SedeLocal, Cliente, Vehiculo, Paradero,
    Ruta, RutaParadero, Usuario, Servicio, ConductorDemo,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    if settings.demo_mode:
        raise RuntimeError(
            "Alembic no se usa en modo demo. "
            "Las tablas SQLite se crean automáticamente en el startup de FastAPI."
        )
    return settings.database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
