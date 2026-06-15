from sqlalchemy.orm import Session
from sqlalchemy import text


def get_conductores_by_sede(sede_id: int, db: Session) -> list[dict]:
    """
    Consulta conductores activos de T_EMPLEADOS para una sede.
    Usa STRING_SPLIT sobre el campo PG_SEDE.locales para mapear
    emp_local_id sin depender de la tabla 'locales' directamente.
    """
    # Usamos CHARINDEX en vez de STRING_SPLIT para compatibilidad
    # con SQL Server 2008 (nivel de compatibilidad 100).
    # La expresión ',' + valor + ',' evita falsos positivos
    # (ej: local_id=2 no coincide con "12" o "22").
    query = text("""
        SELECT
            e.emp_id,
            RTRIM(e.emp_apellidos) + ', ' + RTRIM(e.emp_nombre) AS nombre_completo,
            e.emp_licencia,
            e.emp_licencia_cat,
            e.emp_telefono
        FROM T_EMPLEADOS e
        INNER JOIN PG_SEDE s ON s.sede_id = :sede_id
        WHERE e.emp_carg_id = 3
          AND e.emp_estado  = 'Activo'
          AND CHARINDEX(
                ',' + CAST(e.emp_local_id AS VARCHAR) + ',',
                ',' + s.locales + ','
              ) > 0
        ORDER BY e.emp_apellidos, e.emp_nombre
    """)
    result = db.execute(query, {"sede_id": sede_id})
    rows = result.mappings().all()
    return [dict(r) for r in rows]


def get_conductor_by_id(emp_id: int, db: Session) -> dict | None:
    """
    Obtiene datos de un conductor específico desde T_EMPLEADOS.
    """
    query = text("""
        SELECT
            e.emp_id,
            TRIM(e.emp_apellidos) + ', ' + TRIM(e.emp_nombre) AS nombre_completo,
            e.emp_licencia,
            e.emp_licencia_cat,
            e.emp_telefono
        FROM T_EMPLEADOS e
        WHERE e.emp_id     = :emp_id
          AND e.emp_carg_id = 3
          AND e.emp_estado  = 'Activo'
    """)
    result = db.execute(query, {"emp_id": emp_id})
    row = result.mappings().first()
    return dict(row) if row else None
