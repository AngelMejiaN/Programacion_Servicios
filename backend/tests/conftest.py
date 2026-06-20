"""
conftest.py
===========
Configura el entorno para los tests antes de cualquier importación del backend.
- DEMO_MODE=true → evita intentar conectar a SQL Server durante los tests.
- El motor SQLite se crea pero no se usa (las pruebas son unitarias con mocks).
"""
import os
import sys

# Asegurar que la raíz del proyecto esté en el path para imports absolutos.
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Activar demo mode para que database.py use SQLite y no exija credenciales.
os.environ.setdefault("DEMO_MODE", "true")
