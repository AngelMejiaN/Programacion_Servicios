"""
TransitPro — API principal
==========================
Arranca con:  uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base

# Importar todos los modelos para que SQLAlchemy los registre antes de
# cualquier operación con la base de datos (aunque el schema se crea
# con el script SQL, esto garantiza que las relaciones ORM estén listas).
from .models import (  # noqa: F401
    sede, cliente, vehiculo, paradero,
    ruta, ruta_paradero, usuario, servicio,
)

from .routers import (
    sedes, clientes, vehiculos, paraderos,
    rutas, conductores, usuarios, servicios,
)
from .routers import auth

# ─────────────────────────────────────────────
# Aplicación FastAPI
# ─────────────────────────────────────────────
app = FastAPI(
    title="TransitPro API",
    description=(
        "Sistema de programación de transporte de personal. "
        "Gestiona servicios diarios para múltiples sedes "
        "(Lima, Pisco, Cañete y futuras expansiones)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────
# CORS — ajustar origins en producción
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # En prod: lista de dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(sedes.router)
app.include_router(clientes.router)
app.include_router(vehiculos.router)
app.include_router(paraderos.router)
app.include_router(rutas.router)
app.include_router(conductores.router)
app.include_router(usuarios.router)
app.include_router(servicios.router)


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": "TransitPro API",
        "version": "1.0.0",
    }
