"""
demo_seed.py
============
Siembra la base de datos SQLite con datos de demostración.
Se ejecuta automáticamente en el startup cuando DEMO_MODE=true.
Es idempotente: si la BD ya tiene datos, no inserta nada.
"""
from __future__ import annotations

from datetime import date, time, timedelta

from sqlalchemy.orm import Session

from .auth import hash_password
from .models.sede import Sede
from .models.sede_local import SedeLocal
from .models.cliente import Cliente
from .models.vehiculo import Vehiculo
from .models.paradero import Paradero
from .models.ruta import Ruta
from .models.ruta_paradero import RutaParadero
from .models.usuario import Usuario
from .models.conductor_demo import ConductorDemo
from .models.servicio import Servicio


def seed(db: Session) -> None:
    if db.query(Sede).count() > 0:
        return  # ya sembrado

    # ── Sedes ─────────────────────────────────────────────────────────────────
    lima   = Sede(nombre="Lima",   tipo="A", locales="2",  activa=True)
    pisco  = Sede(nombre="Pisco",  tipo="B", locales="3",  activa=True)
    canete = Sede(nombre="Cañete", tipo="C", locales="38", activa=True)
    db.add_all([lima, pisco, canete])
    db.flush()

    # SedeLocal — tabla relacional que reemplaza el CSV "locales"
    db.add_all([
        SedeLocal(sede_id=lima.sede_id,   local_id=2),
        SedeLocal(sede_id=pisco.sede_id,  local_id=3),
        SedeLocal(sede_id=canete.sede_id, local_id=38),
    ])

    # ── Clientes ──────────────────────────────────────────────────────────────
    cli_lima1  = Cliente(nombre="Industrias Lima Norte SAC",  activo=True)
    cli_lima2  = Cliente(nombre="Envases Pacifico SAC",        activo=True)
    cli_lima3  = Cliente(nombre="Maquinaria Industrial SAC",   activo=True)
    cli_pisco1 = Cliente(nombre="Metalurgica del Sur SAC",     activo=True)
    cli_pisco2 = Cliente(nombre="Procesos Quimicos SAC",       activo=True)
    cli_min1   = Cliente(nombre="Minera Altiplano SAC",        activo=True)
    cli_can1   = Cliente(nombre="Agroindustria Costa SAC",     activo=True)
    db.add_all([cli_lima1, cli_lima2, cli_lima3, cli_pisco1, cli_pisco2, cli_min1, cli_can1])
    db.flush()

    # ── Vehículos ─────────────────────────────────────────────────────────────
    def _bus(placa, sede_id, operativo=True):
        return Vehiculo(placa=placa, marca="MERCEDES", modelo="OF 1721 E5",
                        anio=2019, tipo="BUS", categoria="BUS URBANO",
                        color="BLANCO", sede_id=sede_id, operativo=operativo)

    def _van(placa, sede_id, operativo=True):
        return Vehiculo(placa=placa, marca="MAXUS", modelo="V-80",
                        anio=2020, tipo="VAN", categoria="VAN",
                        color="BLANCO", sede_id=sede_id, operativo=operativo)

    veh_lima = [
        _bus("LIM-001", lima.sede_id),  _bus("LIM-002", lima.sede_id),
        _bus("LIM-003", lima.sede_id),  _bus("LIM-004", lima.sede_id),
        _van("LIM-005", lima.sede_id),  _van("LIM-006", lima.sede_id),
        _bus("LIM-007", lima.sede_id, operativo=False),
    ]
    veh_pisco = [
        _bus("PIS-001", pisco.sede_id), _bus("PIS-002", pisco.sede_id),
        _van("PIS-003", pisco.sede_id), _van("PIS-004", pisco.sede_id),
        _bus("PIS-005", pisco.sede_id, operativo=False),
    ]
    veh_canete = [
        _bus("CAN-001", canete.sede_id), _bus("CAN-002", canete.sede_id),
        _van("CAN-003", canete.sede_id),
    ]
    db.add_all(veh_lima + veh_pisco + veh_canete)
    db.flush()

    # ── Paraderos (Pisco — para rutas variables Tipo B) ───────────────────────
    par_pisco = []
    nombres_paraderos = [
        "Paradero Norte 1", "Paradero Norte 2", "Paradero Centro 1",
        "Paradero Centro 2", "Paradero Sur 1",   "Paradero Sur 2",
        "Paradero Este 1",  "Paradero Este 2",   "Paradero Oeste 1",
        "Paradero Oeste 2", "Paradero Destino",
    ]
    for nombre in nombres_paraderos:
        p = Paradero(nombre=nombre, sede_id=pisco.sede_id, activo=True)
        db.add(p)
        par_pisco.append(p)
    db.flush()

    # Paraderos Cañete (para rutas Tipo C)
    par_can_orig1 = Paradero(nombre="Entrada Norte Planta", sede_id=canete.sede_id, activo=True)
    par_can_orig2 = Paradero(nombre="Entrada Sur Planta",   sede_id=canete.sede_id, activo=True)
    par_can_dest  = Paradero(nombre="Planta Principal",      sede_id=canete.sede_id, activo=True)
    db.add_all([par_can_orig1, par_can_orig2, par_can_dest])
    db.flush()

    # ── Rutas ─────────────────────────────────────────────────────────────────

    # Lima Tipo A — origen fijo, calcula hora llegada
    ruta_a1 = Ruta(nombre="CALLAO",       sede_id=lima.sede_id,   cliente_id=cli_lima2.cliente_id,
                   origen_fijo=True, origen_texto="Sede Lima",
                   tiempo_estimado_min=105, calcula_llegada=True,
                   requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    ruta_a2 = Ruta(nombre="SANTA ANITA",  sede_id=lima.sede_id,   cliente_id=cli_lima2.cliente_id,
                   origen_fijo=True, origen_texto="Sede Lima",
                   tiempo_estimado_min=75,  calcula_llegada=True,
                   requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    ruta_a3 = Ruta(nombre="SJL",          sede_id=lima.sede_id,   cliente_id=cli_lima1.cliente_id,
                   origen_fijo=True, origen_texto="Sede Lima",
                   tiempo_estimado_min=97,  calcula_llegada=True,
                   requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    ruta_mina = Ruta(nombre="RUTA MINA 1", sede_id=lima.sede_id,  cliente_id=cli_min1.cliente_id,
                     origen_fijo=True, origen_texto="Sede Lima",
                     tiempo_estimado_min=None, calcula_llegada=True,
                     requiere_dos_conductores=True, tipo_servicio="MINAS", activa=True)
    db.add_all([ruta_a1, ruta_a2, ruta_a3, ruta_mina])

    # Pisco Tipo B — fija + variable
    ruta_b_fija = Ruta(nombre="RUTA PREMIUM",  sede_id=pisco.sede_id,  cliente_id=cli_pisco2.cliente_id,
                       origen_fijo=True, origen_texto="Planta Quimicos",
                       destino_texto="Sede Pisco", calcula_llegada=False,
                       requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    ruta_b_var  = Ruta(nombre="Ruta A Variable", sede_id=pisco.sede_id, cliente_id=cli_pisco1.cliente_id,
                       origen_fijo=False, destino_texto="Planta Cliente Sur",
                       calcula_llegada=False,
                       requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    db.add_all([ruta_b_fija, ruta_b_var])

    # Cañete Tipo C — combos origen-destino predefinidos
    ruta_c1 = Ruta(nombre="Entrada Norte → Planta Principal",
                   sede_id=canete.sede_id, cliente_id=cli_can1.cliente_id,
                   origen_fijo=True,
                   paradero_origen_id=None, paradero_destino_id=None,
                   calcula_llegada=False,
                   requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    ruta_c2 = Ruta(nombre="Entrada Sur → Planta Principal",
                   sede_id=canete.sede_id, cliente_id=cli_can1.cliente_id,
                   origen_fijo=True,
                   paradero_origen_id=None, paradero_destino_id=None,
                   calcula_llegada=False,
                   requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    db.add_all([ruta_c1, ruta_c2])
    db.flush()

    # Paraderos de la ruta variable de Pisco
    for orden, paradero in enumerate(par_pisco[:-1], start=1):
        db.add(RutaParadero(ruta_id=ruta_b_var.ruta_id,
                            paradero_id=paradero.paradero_id, orden=orden))

    # Asignar paradero_origen_id/destino_id a rutas Cañete ahora que están creados
    ruta_c1.paradero_origen_id  = par_can_orig1.paradero_id
    ruta_c1.paradero_destino_id = par_can_dest.paradero_id
    ruta_c2.paradero_origen_id  = par_can_orig2.paradero_id
    ruta_c2.paradero_destino_id = par_can_dest.paradero_id

    # ── Conductores demo ──────────────────────────────────────────────────────
    conductores_data = [
        # Lima (sede 1) — emp_id 1001–1005
        (1001, "GARCIA LOPEZ, Carlos",    "Q03-05678", "AIII", lima.sede_id),
        (1002, "RAMIREZ TORRES, Luis",    "Q03-12345", "AIII", lima.sede_id),
        (1003, "FLORES QUISPE, Pedro",    "Q03-23456", "AIII", lima.sede_id),
        (1004, "VARGAS MENDEZ, Juan",     "Q03-34567", "AIII", lima.sede_id),
        (1005, "MORA HUANCA, Roberto",    "Q03-45678", "AIII", lima.sede_id),
        # Pisco (sede 2) — emp_id 2001–2005
        (2001, "CASTILLO VERA, Miguel",   "Q03-56789", "AIII", pisco.sede_id),
        (2002, "SALINAS PUMA, Ernesto",   "Q03-67890", "AIII", pisco.sede_id),
        (2003, "REYES CONDORI, Omar",     "Q03-78901", "AIII", pisco.sede_id),
        (2004, "CANO MAMANI, Victor",     "Q03-89012", "AIII", pisco.sede_id),
        (2005, "DIAZ CHOQUE, Fernando",   "Q03-90123", "AIII", pisco.sede_id),
        # Cañete (sede 3) — emp_id 3001–3003
        (3001, "PAREDES NINA, Alex",      "Q03-01234", "AIII", canete.sede_id),
        (3002, "TELLO APAZA, Marco",      "Q03-11223", "AIII", canete.sede_id),
        (3003, "HUANCA QUISPE, Daniel",   "Q03-22334", "AIII", canete.sede_id),
    ]
    for emp_id, nombre, licencia, cat, sede_id in conductores_data:
        db.add(ConductorDemo(emp_id=emp_id, nombre_completo=nombre,
                             emp_licencia=licencia, emp_licencia_cat=cat,
                             sede_id=sede_id, activo=True))

    # ── Usuarios ──────────────────────────────────────────────────────────────
    admin_hash = hash_password("Admin123")
    admin = Usuario(nombre="Administrador", email="admin@transitpro.local",
                    password_hash=admin_hash, rol="administrador",
                    sede_id=lima.sede_id, activo=True)
    db.add(admin)
    db.add_all([
        Usuario(nombre="Programador Lima",   email="prog.lima@transitpro.local",
                password_hash=hash_password("Prog123"), rol="programador",
                sede_id=lima.sede_id, activo=True),
        Usuario(nombre="Programador Pisco",  email="prog.pisco@transitpro.local",
                password_hash=hash_password("Prog123"), rol="programador",
                sede_id=pisco.sede_id, activo=True),
        Usuario(nombre="Programador Cañete", email="prog.canete@transitpro.local",
                password_hash=hash_password("Prog123"), rol="programador",
                sede_id=canete.sede_id, activo=True),
        # Conductor de ejemplo — añadir telegram_id real para activar notificaciones
        Usuario(nombre="Garcia Lopez, Carlos", email=None,
                rol="conductor", emp_id=1001, telegram_id=None,
                sede_id=lima.sede_id, activo=True),
    ])
    db.flush()

    # ── Servicios de demo (mañana) ────────────────────────────────────────────
    manana = date.today() + timedelta(days=1)
    demo_servicios = [
        Servicio(fecha=manana, ruta_id=ruta_a1.ruta_id, sede_id=lima.sede_id,
                 vehiculo_id=veh_lima[0].vehiculo_id, conductor_id=1001,
                 hora_inicio=time(6, 0), hora_llegada_est=time(7, 45),
                 estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_a2.ruta_id, sede_id=lima.sede_id,
                 vehiculo_id=veh_lima[1].vehiculo_id, conductor_id=1002,
                 hora_inicio=time(7, 0), hora_llegada_est=time(8, 15),
                 estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_a3.ruta_id, sede_id=lima.sede_id,
                 vehiculo_id=veh_lima[2].vehiculo_id, conductor_id=1003,
                 hora_inicio=time(5, 30), hora_llegada_est=time(7, 7),
                 estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_b_fija.ruta_id, sede_id=pisco.sede_id,
                 vehiculo_id=veh_pisco[0].vehiculo_id, conductor_id=2001,
                 hora_inicio=time(6, 30), estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_b_var.ruta_id, sede_id=pisco.sede_id,
                 vehiculo_id=veh_pisco[1].vehiculo_id, conductor_id=2002,
                 paradero_origen_id=par_pisco[0].paradero_id,
                 hora_inicio=time(7, 0), estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_c1.ruta_id, sede_id=canete.sede_id,
                 vehiculo_id=veh_canete[0].vehiculo_id, conductor_id=3001,
                 hora_inicio=time(5, 0), estado="PROGRAMADO", creado_por=admin.usuario_id),
    ]
    db.add_all(demo_servicios)

    db.commit()
