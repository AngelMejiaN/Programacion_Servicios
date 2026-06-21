"""
demo_seed.py
============
Siembra la base de datos SQLite con datos de demostración.
Se ejecuta automáticamente en el startup cuando DEMO_MODE=true.
Es idempotente: si la BD ya tiene datos, no inserta nada.

Volumen de stress test:
  - 300 vehículos Lima  (LIM-001 a LIM-300)
  - 300 conductores Lima + 5 Pisco + 3 Cañete
  - 15 rutas Lima + 2 Pisco + 2 Cañete
  - ~12 600 servicios para Junio 2026
      Días 1-20  → COMPLETADO / CANCELADO (75/25 %)
      Día 21     → mix de los 4 estados
      Días 22-30 → PROGRAMADO
"""
from __future__ import annotations

import random
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

# ── Tablas de generación dinámica ─────────────────────────────────────────────

_APELLIDOS = [
    "GARCIA",    "RODRIGUEZ",  "LOPEZ",    "MARTINEZ", "GONZALEZ",
    "PEREZ",     "SANCHEZ",    "RAMIREZ",  "TORRES",   "FLORES",
    "RIVERA",    "GOMEZ",      "DIAZ",     "REYES",    "MORALES",
    "JIMENEZ",   "RUIZ",       "HERRERA",  "MEDINA",   "ROJAS",
    "QUISPE",    "MAMANI",     "HUANCA",   "CONDORI",  "APAZA",
    "CHOQUE",    "PUMA",       "NINA",     "CANO",     "SOTO",
]
_NOMBRES = [
    "Carlos",  "Juan",     "Pedro",   "Luis",    "Miguel",
    "Jose",    "Fernando", "Ricardo", "Eduardo", "Roberto",
    "Manuel",  "David",    "Jorge",   "Oscar",   "Hugo",
    "Antonio", "Victor",   "Sergio",  "Hector",  "Alex",
    "Daniel",  "Marco",    "Andres",  "Diego",   "Rafael",
    "Cesar",   "Felix",    "Raul",    "Abel",    "Moises",
]
_MARCAS_MODELOS = [
    ("MERCEDES",   "OF 1721 E5"),
    ("SCANIA",     "K310 IB"),
    ("HYUNDAI",    "COUNTY"),
    ("VOLKSWAGEN", "17.250 OD"),
    ("KING LONG",  "XMQ6900"),
    ("YUTONG",     "ZK6108"),
    ("MODASA",     "ZEUS IV"),
]
_HORAS_AM = [time(h, m) for h in range(5, 11) for m in (0, 15, 30, 45)]
_HORAS_PM = [time(h, m) for h in range(13, 19) for m in (0, 15, 30, 45)]

_DIA_ANCLA = 21  # "hoy" dentro del mes de Junio 2026


def _add_minutes(t: time, minutes: int) -> time:
    total = t.hour * 60 + t.minute + minutes
    return time(total // 60 % 24, total % 60)


def _estado_junio(day: int) -> str:
    if day < _DIA_ANCLA:
        return random.choices(["COMPLETADO", "CANCELADO"], weights=[75, 25])[0]
    if day == _DIA_ANCLA:
        return random.choices(
            ["PROGRAMADO", "EN_CURSO", "COMPLETADO", "CANCELADO"],
            weights=[35, 20, 35, 10],
        )[0]
    return "PROGRAMADO"


# ─────────────────────────────────────────────────────────────────────────────

def seed(db: Session) -> None:
    if db.query(Sede).count() > 0:
        return  # ya sembrado — borrar demo.db para regenerar

    random.seed(42)

    # ── Sedes ─────────────────────────────────────────────────────────────────
    lima   = Sede(nombre="Lima",   tipo="A", locales="2",  activa=True)
    pisco  = Sede(nombre="Pisco",  tipo="B", locales="3",  activa=True)
    canete = Sede(nombre="Cañete", tipo="C", locales="38", activa=True)
    db.add_all([lima, pisco, canete])
    db.flush()

    db.add_all([
        SedeLocal(sede_id=lima.sede_id,   local_id=2),
        SedeLocal(sede_id=pisco.sede_id,  local_id=3),
        SedeLocal(sede_id=canete.sede_id, local_id=38),
    ])

    # ── Clientes ──────────────────────────────────────────────────────────────
    cli_lima1  = Cliente(nombre="Industrias Lima Norte SAC", activo=True)
    cli_lima2  = Cliente(nombre="Envases Pacifico SAC",       activo=True)
    cli_lima3  = Cliente(nombre="Maquinaria Industrial SAC",  activo=True)
    cli_pisco1 = Cliente(nombre="Metalurgica del Sur SAC",    activo=True)
    cli_pisco2 = Cliente(nombre="Procesos Quimicos SAC",      activo=True)
    cli_min1   = Cliente(nombre="Minera Altiplano SAC",       activo=True)
    cli_can1   = Cliente(nombre="Agroindustria Costa SAC",    activo=True)
    db.add_all([cli_lima1, cli_lima2, cli_lima3,
                cli_pisco1, cli_pisco2, cli_min1, cli_can1])
    db.flush()

    # ── Vehículos Lima — 300 unidades (LIM-001 a LIM-300) ─────────────────────
    veh_lima = []
    for i in range(1, 301):
        marca, modelo = _MARCAS_MODELOS[i % len(_MARCAS_MODELOS)]
        v = Vehiculo(
            placa      = f"LIM-{i:03d}",
            marca      = marca,
            modelo     = modelo,
            anio       = 2014 + (i % 10),
            tipo       = "VAN" if i % 6 == 0 else "BUS",
            categoria  = "VAN" if i % 6 == 0 else "BUS URBANO",
            color      = "BLANCO",
            sede_id    = lima.sede_id,
            operativo  = (i % 10 != 0),   # 90 % operativos
        )
        db.add(v)
        veh_lima.append(v)

    # ── Vehículos Pisco y Cañete ───────────────────────────────────────────────
    def _bus(placa, sede_id, operativo=True):
        return Vehiculo(placa=placa, marca="MERCEDES", modelo="OF 1721 E5",
                        anio=2019, tipo="BUS", categoria="BUS URBANO",
                        color="BLANCO", sede_id=sede_id, operativo=operativo)

    def _van(placa, sede_id, operativo=True):
        return Vehiculo(placa=placa, marca="MAXUS", modelo="V-80",
                        anio=2020, tipo="VAN", categoria="VAN",
                        color="BLANCO", sede_id=sede_id, operativo=operativo)

    veh_pisco = [
        _bus("PIS-001", pisco.sede_id), _bus("PIS-002", pisco.sede_id),
        _van("PIS-003", pisco.sede_id), _van("PIS-004", pisco.sede_id),
        _bus("PIS-005", pisco.sede_id, operativo=False),
    ]
    veh_canete = [
        _bus("CAN-001", canete.sede_id), _bus("CAN-002", canete.sede_id),
        _van("CAN-003", canete.sede_id),
    ]
    db.add_all(veh_pisco + veh_canete)
    db.flush()

    # ── Paraderos ─────────────────────────────────────────────────────────────
    par_pisco = []
    for nombre in [
        "Paradero Norte 1", "Paradero Norte 2", "Paradero Centro 1",
        "Paradero Centro 2", "Paradero Sur 1",   "Paradero Sur 2",
        "Paradero Este 1",  "Paradero Este 2",   "Paradero Oeste 1",
        "Paradero Oeste 2", "Paradero Destino",
    ]:
        p = Paradero(nombre=nombre, sede_id=pisco.sede_id, activo=True)
        db.add(p)
        par_pisco.append(p)

    par_can_orig1 = Paradero(nombre="Entrada Norte Planta", sede_id=canete.sede_id, activo=True)
    par_can_orig2 = Paradero(nombre="Entrada Sur Planta",   sede_id=canete.sede_id, activo=True)
    par_can_dest  = Paradero(nombre="Planta Principal",      sede_id=canete.sede_id, activo=True)
    db.add_all([par_can_orig1, par_can_orig2, par_can_dest])
    db.flush()

    # ── Rutas Lima — 15 destinos ───────────────────────────────────────────────
    def _ruta_lima(nombre, cliente, tiempo, dos_cond=False):
        return Ruta(
            nombre=nombre, sede_id=lima.sede_id, cliente_id=cliente.cliente_id,
            origen_fijo=True, origen_texto="Sede Lima",
            tiempo_estimado_min=tiempo, calcula_llegada=True,
            requiere_dos_conductores=dos_cond,
            tipo_servicio="PERSONAL" if not dos_cond else "MINAS",
            activa=True,
        )

    rutas_lima = [
        _ruta_lima("CALLAO",        cli_lima2, 105),
        _ruta_lima("SANTA ANITA",   cli_lima2,  75),
        _ruta_lima("SJL",           cli_lima1,  97),
        _ruta_lima("RUTA MINA 1",   cli_min1,  None, dos_cond=True),
        _ruta_lima("ATE",           cli_lima1,  65),
        _ruta_lima("CHORRILLOS",    cli_lima3,  80),
        _ruta_lima("SAN MIGUEL",    cli_lima2,  55),
        _ruta_lima("LOS OLIVOS",    cli_lima1,  70),
        _ruta_lima("CARABAYLLO",    cli_lima1, 105),
        _ruta_lima("MIRAFLORES",    cli_lima3,  60),
        _ruta_lima("LA MOLINA",     cli_lima3,  85),
        _ruta_lima("SURCO",         cli_lima3,  75),
        _ruta_lima("RIMAC",         cli_lima2,  50),
        _ruta_lima("VILLA MARIA",   cli_lima1,  90),
        _ruta_lima("INDEPENDENCIA", cli_lima2,  65),
    ]
    db.add_all(rutas_lima)

    # ── Rutas Pisco y Cañete ──────────────────────────────────────────────────
    ruta_b_fija = Ruta(nombre="RUTA PREMIUM", sede_id=pisco.sede_id,
                       cliente_id=cli_pisco2.cliente_id,
                       origen_fijo=True, origen_texto="Planta Quimicos",
                       destino_texto="Sede Pisco", calcula_llegada=False,
                       requiere_dos_conductores=False,
                       tipo_servicio="PERSONAL", activa=True)
    ruta_b_var  = Ruta(nombre="Ruta A Variable", sede_id=pisco.sede_id,
                       cliente_id=cli_pisco1.cliente_id,
                       origen_fijo=False, destino_texto="Planta Cliente Sur",
                       calcula_llegada=False,
                       requiere_dos_conductores=False,
                       tipo_servicio="PERSONAL", activa=True)
    ruta_c1 = Ruta(nombre="Entrada Norte → Planta Principal",
                   sede_id=canete.sede_id, cliente_id=cli_can1.cliente_id,
                   origen_fijo=True, paradero_origen_id=None,
                   paradero_destino_id=None, calcula_llegada=False,
                   requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    ruta_c2 = Ruta(nombre="Entrada Sur → Planta Principal",
                   sede_id=canete.sede_id, cliente_id=cli_can1.cliente_id,
                   origen_fijo=True, paradero_origen_id=None,
                   paradero_destino_id=None, calcula_llegada=False,
                   requiere_dos_conductores=False, tipo_servicio="PERSONAL", activa=True)
    db.add_all([ruta_b_fija, ruta_b_var, ruta_c1, ruta_c2])
    db.flush()

    for orden, par in enumerate(par_pisco[:-1], start=1):
        db.add(RutaParadero(ruta_id=ruta_b_var.ruta_id,
                            paradero_id=par.paradero_id, orden=orden))
    ruta_c1.paradero_origen_id   = par_can_orig1.paradero_id
    ruta_c1.paradero_destino_id  = par_can_dest.paradero_id
    ruta_c2.paradero_origen_id   = par_can_orig2.paradero_id
    ruta_c2.paradero_destino_id  = par_can_dest.paradero_id

    # ── Conductores Lima — 300 (emp_id 1001-1300) ─────────────────────────────
    # Los primeros 5 mantienen nombre e ID histórico (referenciados en servicios demo).
    _COND_BASE = [
        (1001, "GARCIA LOPEZ, Carlos",  "Q03-05678", "AIII"),
        (1002, "RAMIREZ TORRES, Luis",  "Q03-12345", "AIII"),
        (1003, "FLORES QUISPE, Pedro",  "Q03-23456", "AIII"),
        (1004, "VARGAS MENDEZ, Juan",   "Q03-34567", "AIII"),
        (1005, "MORA HUANCA, Roberto",  "Q03-45678", "AIII"),
    ]
    cond_lima_ids = [r[0] for r in _COND_BASE]
    for emp_id, nombre, lic, cat in _COND_BASE:
        db.add(ConductorDemo(emp_id=emp_id, nombre_completo=nombre,
                             emp_licencia=lic, emp_licencia_cat=cat,
                             sede_id=lima.sede_id, activo=True))

    # Conductores 1006-1300: generados por combinación de apellido × nombre
    # 30 apellidos × 10 rondas = 300; usamos 295 (1006..1300)
    for i in range(295):
        ap  = _APELLIDOS[i % 30]
        nm  = _NOMBRES[(i // 30) % 10]
        eid = 1006 + i
        db.add(ConductorDemo(
            emp_id          = eid,
            nombre_completo = f"{ap}, {nm}",
            emp_licencia    = f"Q03-{10000 + i:05d}",
            emp_licencia_cat= "AIII",
            sede_id         = lima.sede_id,
            activo          = True,
        ))
        cond_lima_ids.append(eid)

    # ── Conductores Pisco y Cañete ────────────────────────────────────────────
    for emp_id, nombre, lic, cat, sid in [
        (2001, "CASTILLO VERA, Miguel",  "Q03-56789", "AIII", pisco.sede_id),
        (2002, "SALINAS PUMA, Ernesto",  "Q03-67890", "AIII", pisco.sede_id),
        (2003, "REYES CONDORI, Omar",    "Q03-78901", "AIII", pisco.sede_id),
        (2004, "CANO MAMANI, Victor",    "Q03-89012", "AIII", pisco.sede_id),
        (2005, "DIAZ CHOQUE, Fernando",  "Q03-90123", "AIII", pisco.sede_id),
        (3001, "PAREDES NINA, Alex",     "Q03-01234", "AIII", canete.sede_id),
        (3002, "TELLO APAZA, Marco",     "Q03-11223", "AIII", canete.sede_id),
        (3003, "HUANCA QUISPE, Daniel",  "Q03-22334", "AIII", canete.sede_id),
    ]:
        db.add(ConductorDemo(emp_id=emp_id, nombre_completo=nombre,
                             emp_licencia=lic, emp_licencia_cat=cat,
                             sede_id=sid, activo=True))

    # ── Usuarios ──────────────────────────────────────────────────────────────
    admin = Usuario(nombre="Administrador", email="admin@transitpro.local",
                    password_hash=hash_password("Admin123"), rol="administrador",
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
        Usuario(nombre="Garcia Lopez, Carlos", email=None, rol="conductor",
                emp_id=1001, telegram_id=None, sede_id=lima.sede_id, activo=True),
    ])
    db.flush()

    # ── Servicios de demo para mañana (compatibilidad) ─────────────────────────
    manana = date.today() + timedelta(days=1)
    db.add_all([
        Servicio(fecha=manana, ruta_id=rutas_lima[0].ruta_id, sede_id=lima.sede_id,
                 vehiculo_id=veh_lima[0].vehiculo_id, conductor_id=1001,
                 hora_inicio=time(6, 0), hora_llegada_est=time(7, 45),
                 estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=rutas_lima[1].ruta_id, sede_id=lima.sede_id,
                 vehiculo_id=veh_lima[1].vehiculo_id, conductor_id=1002,
                 hora_inicio=time(7, 0), hora_llegada_est=time(8, 15),
                 estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=rutas_lima[2].ruta_id, sede_id=lima.sede_id,
                 vehiculo_id=veh_lima[2].vehiculo_id, conductor_id=1003,
                 hora_inicio=time(5, 30), hora_llegada_est=time(7, 7),
                 estado="PROGRAMADO", creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_b_fija.ruta_id, sede_id=pisco.sede_id,
                 vehiculo_id=veh_pisco[0].vehiculo_id, conductor_id=2001,
                 hora_inicio=time(6, 30), estado="PROGRAMADO",
                 creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_b_var.ruta_id, sede_id=pisco.sede_id,
                 vehiculo_id=veh_pisco[1].vehiculo_id, conductor_id=2002,
                 paradero_origen_id=par_pisco[0].paradero_id,
                 hora_inicio=time(7, 0), estado="PROGRAMADO",
                 creado_por=admin.usuario_id),
        Servicio(fecha=manana, ruta_id=ruta_c1.ruta_id, sede_id=canete.sede_id,
                 vehiculo_id=veh_canete[0].vehiculo_id, conductor_id=3001,
                 hora_inicio=time(5, 0), estado="PROGRAMADO",
                 creado_por=admin.usuario_id),
    ])

    # ── Servicios masivos — Junio 2026 (stress test) ──────────────────────────
    # 300 turno AM + 120 turno PM = 420 servicios/día × 30 días = 12 600 servicios
    veh_ids      = [v.vehiculo_id for v in veh_lima]  # 300 IDs de vehículos Lima
    ruta_ids     = [r.ruta_id for r in rutas_lima]    # 15 IDs de rutas Lima
    cid_pool     = list(cond_lima_ids)                 # 300 IDs de conductores Lima
    ruta_tiempo  = {r.ruta_id: r.tiempo_estimado_min for r in rutas_lima}

    servicios_junio: list[Servicio] = []

    for day in range(1, 31):
        fecha = date(2026, 6, day)

        # Turno AM — 1 servicio por vehículo (300 servicios)
        r_veh  = list(veh_ids);  random.shuffle(r_veh)
        r_cond = list(cid_pool); random.shuffle(r_cond)

        for idx, (vid, cid) in enumerate(zip(r_veh, r_cond)):
            rid    = ruta_ids[idx % len(ruta_ids)]
            hora   = random.choice(_HORAS_AM)
            estado = _estado_junio(day)
            tiempo = ruta_tiempo.get(rid)
            hora_est  = _add_minutes(hora, tiempo) if tiempo else None
            hora_real = None
            if estado == 'COMPLETADO' and hora_est:
                delta = random.randint(-10, 0) if random.random() < 0.92 else random.randint(5, 30)
                hora_real = _add_minutes(hora_est, delta)
            servicios_junio.append(Servicio(
                fecha             = fecha,
                ruta_id           = rid,
                sede_id           = lima.sede_id,
                vehiculo_id       = vid,
                conductor_id      = cid,
                hora_inicio       = hora,
                hora_llegada_est  = hora_est,
                hora_llegada_real = hora_real,
                estado            = estado,
                creado_por        = admin.usuario_id,
            ))

        # Turno PM — 40 % de la flota con segundo servicio (120 servicios)
        pm_veh  = random.sample(veh_ids,  120)
        pm_cond = random.sample(cid_pool, 120)
        for vid, cid in zip(pm_veh, pm_cond):
            rid    = random.choice(ruta_ids)
            hora   = random.choice(_HORAS_PM)
            estado = _estado_junio(day)
            tiempo = ruta_tiempo.get(rid)
            hora_est  = _add_minutes(hora, tiempo) if tiempo else None
            hora_real = None
            if estado == 'COMPLETADO' and hora_est:
                delta = random.randint(-10, 0) if random.random() < 0.92 else random.randint(5, 30)
                hora_real = _add_minutes(hora_est, delta)
            servicios_junio.append(Servicio(
                fecha             = fecha,
                ruta_id           = rid,
                sede_id           = lima.sede_id,
                vehiculo_id       = vid,
                conductor_id      = cid,
                hora_inicio       = hora,
                hora_llegada_est  = hora_est,
                hora_llegada_real = hora_real,
                estado            = estado,
                creado_por        = admin.usuario_id,
            ))

    # Inserción en lotes de 1 000 para no saturar la sesión
    BATCH = 1_000
    for i in range(0, len(servicios_junio), BATCH):
        db.add_all(servicios_junio[i : i + BATCH])
        db.flush()
    servicios_junio.clear()

    db.commit()
