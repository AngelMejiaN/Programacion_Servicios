from sqlalchemy.orm import Session
from sqlalchemy import text

from ..config import settings


def get_conductores_by_sede(sede_id: int, db: Session, incluir_inactivos: bool = False) -> list[dict]:
    if settings.demo_mode:
        return _conductores_demo(sede_id, db, incluir_inactivos)
    return _conductores_produccion(sede_id, db)


def get_conductor_by_id(emp_id: int, db: Session) -> dict | None:
    if settings.demo_mode:
        return _conductor_demo_by_id(emp_id, db)
    return _conductor_produccion_by_id(emp_id, db)


def create_conductor(data, db: Session) -> dict:
    from ..models.conductor_demo import ConductorDemo
    c = ConductorDemo(
        nombre_completo  = data.nombre_completo,
        emp_licencia     = data.licencia,
        emp_licencia_cat = data.licencia_cat,
        emp_telefono     = data.telefono,
        sede_id          = data.sede_id,
        activo           = True,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _row_to_dict(c)


def update_conductor(emp_id: int, data, db: Session) -> dict | None:
    from ..models.conductor_demo import ConductorDemo
    _FIELD_MAP = {
        "licencia":     "emp_licencia",
        "licencia_cat": "emp_licencia_cat",
        "telefono":     "emp_telefono",
    }
    c = db.query(ConductorDemo).filter(ConductorDemo.emp_id == emp_id).first()
    if not c:
        return None
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(c, _FIELD_MAP.get(campo, campo), valor)
    db.commit()
    db.refresh(c)
    return _row_to_dict(c)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_dict(r) -> dict:
    return {
        "emp_id":          r.emp_id,
        "nombre_completo": r.nombre_completo,
        "licencia":        r.emp_licencia,
        "licencia_cat":    r.emp_licencia_cat,
        "telefono":        r.emp_telefono,
        "activo":          r.activo,
    }


# ── Demo (SQLite) ─────────────────────────────────────────────────────────────

def _conductores_demo(sede_id: int, db: Session, incluir_inactivos: bool = False) -> list[dict]:
    from ..models.conductor_demo import ConductorDemo
    q = db.query(ConductorDemo).filter(ConductorDemo.sede_id == sede_id)
    if not incluir_inactivos:
        q = q.filter(ConductorDemo.activo == True)
    rows = q.order_by(ConductorDemo.nombre_completo).all()
    return [_row_to_dict(r) for r in rows]


def _conductor_demo_by_id(emp_id: int, db: Session) -> dict | None:
    from ..models.conductor_demo import ConductorDemo
    r = db.query(ConductorDemo).filter(
        ConductorDemo.emp_id == emp_id,
        ConductorDemo.activo == True,
    ).first()
    return _row_to_dict(r) if r else None


# ── Producción (SQL Server) ───────────────────────────────────────────────────

def _conductores_produccion(sede_id: int, db: Session) -> list[dict]:
    query = text("""
        SELECT
            e.emp_id,
            RTRIM(e.emp_apellidos) + ', ' + RTRIM(e.emp_nombre) AS nombre_completo,
            e.emp_licencia     AS licencia,
            e.emp_licencia_cat AS licencia_cat,
            e.emp_telefono     AS telefono,
            1 AS activo
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
            e.emp_telefono     AS telefono,
            1 AS activo
        FROM T_EMPLEADOS e
        WHERE e.emp_id      = :emp_id
          AND e.emp_carg_id = 3
          AND e.emp_estado  = 'Activo'
    """)
    result = db.execute(query, {"emp_id": emp_id})
    row = result.mappings().first()
    return dict(row) if row else None
