from sqlalchemy.orm import Session
from sqlalchemy import text

from ..config import settings


def get_conductores_by_sede(sede_id: int, db: Session) -> list[dict]:
    """
    Devuelve conductores activos para una sede.
    - Demo mode  → consulta PG_CONDUCTOR_DEMO (SQLite, sin T_EMPLEADOS).
    - Producción → consulta T_EMPLEADOS usando JOIN con PG_SEDE_LOCAL.
    """
    if settings.demo_mode:
        return _conductores_demo(sede_id, db)
    return _conductores_produccion(sede_id, db)


def get_conductor_by_id(emp_id: int, db: Session) -> dict | None:
    if settings.demo_mode:
        return _conductor_demo_by_id(emp_id, db)
    return _conductor_produccion_by_id(emp_id, db)


# ── Demo (SQLite) ─────────────────────────────────────────────────────────────

def _conductores_demo(sede_id: int, db: Session) -> list[dict]:
    from ..models.conductor_demo import ConductorDemo
    rows = (
        db.query(ConductorDemo)
        .filter(ConductorDemo.sede_id == sede_id, ConductorDemo.activo == True)
        .order_by(ConductorDemo.nombre_completo)
        .all()
    )
    return [
        {
            "emp_id":          r.emp_id,
            "nombre_completo": r.nombre_completo,
            "licencia":        r.emp_licencia,
            "licencia_cat":    r.emp_licencia_cat,
            "telefono":        r.emp_telefono,
        }
        for r in rows
    ]


def _conductor_demo_by_id(emp_id: int, db: Session) -> dict | None:
    from ..models.conductor_demo import ConductorDemo
    r = db.query(ConductorDemo).filter(
        ConductorDemo.emp_id == emp_id,
        ConductorDemo.activo == True,
    ).first()
    if not r:
        return None
    return {
        "emp_id":          r.emp_id,
        "nombre_completo": r.nombre_completo,
        "licencia":        r.emp_licencia,
        "licencia_cat":    r.emp_licencia_cat,
        "telefono":        r.emp_telefono,
    }


# ── Producción (SQL Server) ───────────────────────────────────────────────────

def _conductores_produccion(sede_id: int, db: Session) -> list[dict]:
    """
    Usa JOIN con PG_SEDE_LOCAL en lugar de CHARINDEX sobre la columna locales.
    PG_SEDE_LOCAL.local_id corresponde a T_EMPLEADOS.emp_local_id.
    """
    query = text("""
        SELECT
            e.emp_id,
            RTRIM(e.emp_apellidos) + ', ' + RTRIM(e.emp_nombre) AS nombre_completo,
            e.emp_licencia     AS licencia,
            e.emp_licencia_cat AS licencia_cat,
            e.emp_telefono     AS telefono
        FROM T_EMPLEADOS e
        INNER JOIN PG_SEDE_LOCAL sl
            ON sl.local_id = e.emp_local_id
           AND sl.sede_id  = :sede_id
        WHERE e.emp_carg_id = 3
          AND e.emp_estado  = 'Activo'
        ORDER BY e.emp_apellidos, e.emp_nombre
    """)
    result = db.execute(query, {"sede_id": sede_id})
    return [dict(r) for r in result.mappings().all()]


def _conductor_produccion_by_id(emp_id: int, db: Session) -> dict | None:
    query = text("""
        SELECT
            e.emp_id,
            TRIM(e.emp_apellidos) + ', ' + TRIM(e.emp_nombre) AS nombre_completo,
            e.emp_licencia     AS licencia,
            e.emp_licencia_cat AS licencia_cat,
            e.emp_telefono     AS telefono
        FROM T_EMPLEADOS e
        WHERE e.emp_id      = :emp_id
          AND e.emp_carg_id = 3
          AND e.emp_estado  = 'Activo'
    """)
    result = db.execute(query, {"emp_id": emp_id})
    row = result.mappings().first()
    return dict(row) if row else None
