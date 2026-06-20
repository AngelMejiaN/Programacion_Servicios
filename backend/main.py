"""
TransitPro — API principal
==========================
Arranca con:  uvicorn backend.main:app --reload

Demo sin SQL Server:
  DEMO_MODE=true uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base

from .models import (  # noqa: F401  — registra todos los modelos en Base
    sede, cliente, vehiculo, paradero,
    ruta, ruta_paradero, usuario, servicio,
    sede_local, conductor_demo,
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
# CORS — lista de orígenes desde variable de entorno
# ─────────────────────────────────────────────
_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
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
# Startup — solo en modo demo
# ─────────────────────────────────────────────
@app.on_event("startup")
def _startup():
    if settings.demo_mode:
        Base.metadata.create_all(bind=engine)
        from .demo_seed import seed
        from .database import SessionLocal
        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": "TransitPro API",
        "version": "1.0.0",
        "demo_mode": settings.demo_mode,
    }
