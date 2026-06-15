"""
middleware.py
=============
Autenticación: busca al usuario en PG_USUARIO por su telegram_id.
Retorna None si no está registrado.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

# Importamos los modelos directamente del backend (mismo proyecto)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.usuario import Usuario
from backend.models.sede import Sede
from backend.models.servicio import Servicio
from backend.models.ruta import Ruta
from backend.models.vehiculo import Vehiculo


def get_usuario(telegram_id: int, db: Session) -> Usuario | None:
    """Retorna el usuario activo asociado al telegram_id, o None."""
    return (
        db.query(Usuario)
        .filter(
            Usuario.telegram_id == telegram_id,
            Usuario.activo == True,
        )
        .first()
    )


def es_programador(usuario: Usuario) -> bool:
    return usuario.rol in ("programador", "administrador")


def es_conductor(usuario: Usuario) -> bool:
    return usuario.rol in ("conductor", "programador", "administrador")
