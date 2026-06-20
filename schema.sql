-- ============================================================
-- TransitPro | TransitProDB
-- Script de creación de tablas y datos de referencia
-- Prefijo PG_ para tablas propias del sistema
--
-- Tablas externas usadas (solo lectura, NO modificar):
--   T_EMPLEADOS  → conductores filtrando emp_carg_id = 3
--   locales      → referenciada via campo locales en PG_SEDE
--
-- ⚠️  IMPORTANTE (mantener en futuras versiones):
--   El campo PG_SEDE.locales almacena IDs de la tabla "locales"
--   separados por coma. Estos IDs corresponden a emp_local_id
--   en T_EMPLEADOS y se usan para filtrar conductores por sede.
--   Si se agregan nuevas sedes, consultar la tabla "locales"
--   para identificar los Loc_id correctos y actualizar este campo.
-- ============================================================

USE TransitProDB;
GO

-- ============================================================
-- 1. PG_SEDE
-- ============================================================
CREATE TABLE PG_SEDE (
    sede_id  INT          IDENTITY(1,1) PRIMARY KEY,
    nombre   VARCHAR(100) NOT NULL,
    tipo     CHAR(1)      NOT NULL CHECK (tipo IN ('A','B','C')),
    locales  VARCHAR(50)  NULL,  -- IDs de tabla "locales" separados por coma
    activa   BIT          NOT NULL DEFAULT 1
);
GO

-- ============================================================
-- 2. PG_CLIENTE
-- ============================================================
CREATE TABLE PG_CLIENTE (
    cliente_id  INT          IDENTITY(1,1) PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    ruc         VARCHAR(20)  NULL,
    activo      BIT          NOT NULL DEFAULT 1
);
GO

-- ============================================================
-- 3. PG_VEHICULO
-- ============================================================
CREATE TABLE PG_VEHICULO (
    vehiculo_id INT          IDENTITY(1,1) PRIMARY KEY,
    placa       VARCHAR(10)  NOT NULL,
    marca       VARCHAR(50)  NULL,
    modelo      VARCHAR(50)  NULL,
    anio        INT          NULL,
    tipo        VARCHAR(20)  NULL,
    categoria   VARCHAR(50)  NULL,
    color       VARCHAR(30)  NULL,
    sede_id     INT          NULL REFERENCES PG_SEDE(sede_id),
    operativo   BIT          NOT NULL DEFAULT 1
);
GO

-- ============================================================
-- 4. PG_PARADERO
-- ============================================================
CREATE TABLE PG_PARADERO (
    paradero_id INT          IDENTITY(1,1) PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    direccion   VARCHAR(200) NULL,
    sede_id     INT          NOT NULL REFERENCES PG_SEDE(sede_id),
    activo      BIT          NOT NULL DEFAULT 1
);
GO

-- ============================================================
-- 5. PG_RUTA
-- ============================================================
CREATE TABLE PG_RUTA (
    ruta_id             INT          IDENTITY(1,1) PRIMARY KEY,
    nombre              VARCHAR(100) NOT NULL,
    sede_id             INT          NOT NULL REFERENCES PG_SEDE(sede_id),
    cliente_id          INT          NOT NULL REFERENCES PG_CLIENTE(cliente_id),
    origen_fijo         BIT          NOT NULL DEFAULT 1,
    origen_texto        VARCHAR(200) NULL,
    paradero_origen_id  INT          NULL REFERENCES PG_PARADERO(paradero_id),
    destino_texto       VARCHAR(200) NULL,
    paradero_destino_id INT          NULL REFERENCES PG_PARADERO(paradero_id),
    tiempo_estimado_min INT          NULL,
    calcula_llegada          BIT          NOT NULL DEFAULT 0,
    requiere_dos_conductores BIT          NOT NULL DEFAULT 0,  -- 1 = ruta larga, obliga 2 conductores
    tipo_servicio            VARCHAR(15)  NOT NULL DEFAULT 'PERSONAL'
                             CHECK (tipo_servicio IN ('PERSONAL','MINAS','MINERALES')),
    activa                   BIT          NOT NULL DEFAULT 1
);
GO

-- ============================================================
-- 6. PG_RUTA_PARADERO
-- ============================================================
CREATE TABLE PG_RUTA_PARADERO (
    ruta_id     INT NOT NULL REFERENCES PG_RUTA(ruta_id),
    paradero_id INT NOT NULL REFERENCES PG_PARADERO(paradero_id),
    orden       INT NOT NULL DEFAULT 1,
    PRIMARY KEY (ruta_id, paradero_id)
);
GO

-- ============================================================
-- 7. PG_USUARIO
-- ============================================================
CREATE TABLE PG_USUARIO (
    usuario_id    INT          IDENTITY(1,1) PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NULL UNIQUE,
    password_hash VARCHAR(255) NULL,           -- NULL para usuarios solo-bot
    telegram_id   BIGINT       NULL,
    emp_id        INT          NULL,           -- vincula con T_EMPLEADOS para notificaciones bot
    rol           VARCHAR(20)  NOT NULL CHECK (rol IN ('administrador','programador','supervisor','conductor')),
    sede_id       INT          NULL REFERENCES PG_SEDE(sede_id),
    activo        BIT          NOT NULL DEFAULT 1
);
GO

-- ============================================================
-- 8. PG_SERVICIO
-- ============================================================
CREATE TABLE PG_SERVICIO (
    servicio_id          INT          IDENTITY(1,1) PRIMARY KEY,
    fecha                DATE         NOT NULL,
    ruta_id              INT          NOT NULL REFERENCES PG_RUTA(ruta_id),
    sede_id              INT          NOT NULL REFERENCES PG_SEDE(sede_id),
    vehiculo_id          INT          NOT NULL REFERENCES PG_VEHICULO(vehiculo_id),
    conductor_id         INT          NOT NULL,  -- T_EMPLEADOS.emp_id (sin FK, tabla externa)
    conductor2_id        INT          NULL,       -- segundo conductor (rutas largas de mina)
    paradero_origen_id   INT          NULL REFERENCES PG_PARADERO(paradero_id),
    hora_inicio          TIME         NULL,
    hora_llegada_est     TIME         NULL,
    hora_llegada_real    TIME         NULL,
    hora_fin_manual      TIME         NULL,
    estado               VARCHAR(15)  NOT NULL DEFAULT 'PROGRAMADO'
                         CHECK (estado IN ('PROGRAMADO','EN_CURSO','COMPLETADO','CANCELADO')),
    observaciones        VARCHAR(MAX) NULL,
    creado_por           INT          NULL REFERENCES PG_USUARIO(usuario_id),
    fecha_creacion       DATETIME     NOT NULL DEFAULT GETDATE(),
    fecha_llegada        DATE         NULL,       -- NULL = mismo dia; se llena si el servicio cruza medianoche
    -- Retorno
    fecha_retorno        DATE         NULL,       -- NULL = mismo dia; fecha distinta si pernocte o ruta larga
    retorno_misma_unidad BIT          NOT NULL DEFAULT 1,
    retorno_vehiculo_id  INT          NULL REFERENCES PG_VEHICULO(vehiculo_id),
    retorno_conductor_id  INT          NULL,  -- T_EMPLEADOS.emp_id (sin FK, tabla externa)
    retorno_conductor2_id INT          NULL,  -- segundo conductor en retorno (rutas largas)
    hora_salida_planta   TIME         NULL,
    hora_retorno_est     TIME         NULL,
    hora_retorno_real    TIME         NULL
);
GO

-- ============================================================
-- DATOS DE REFERENCIA
-- ============================================================

-- ------------------------------------------------------------
-- PG_SEDE (piloto)
-- ------------------------------------------------------------
INSERT INTO PG_SEDE (nombre, tipo, locales, activa) VALUES
    ('Lima',   'A', '2',    1),
    ('Pisco',  'B', '3',    1),
    ('Cañete', 'C', '38',   1);
GO

-- ------------------------------------------------------------
-- PG_CLIENTE
-- ------------------------------------------------------------
INSERT INTO PG_CLIENTE (nombre, activo) VALUES
    ('Industrias Lima Norte SAC',     1),  -- Lima
    ('Envases Pacifico SAC',           1),  -- Lima
    ('Automotriz Andina SAC',       1),  -- Lima
    ('Metalurgica del Sur SAC', 1),  -- Lima / Pisco
    ('Maquinaria Industrial SAC',        1),  -- Lima
    ('Plasticos del Centro SAC',        1),  -- Lima
    ('Minera Altiplano SAC',      1),  -- Lima / Huancayo
    ('Minera Cordillera SAC',          1),  -- Lima / Huancayo
    ('Catering Corporativo SAC',        1),  -- Huancayo
    ('Quimicos Callao SAC',         1),  -- Callao
    ('Procesos Quimicos SAC',         1),  -- Pisco
    ('Corporativo Premium SAC',             1),  -- Pisco (RUTA PREMIUM)
    ('Agroindustria Costa SAC',    1),  -- Cañete
    ('Agroexport Valle SAC',            1);  -- Cañete
GO

-- ------------------------------------------------------------
-- PG_PARADERO — Pisco (sede_id = 2)
-- Rutas variables A, B, C (cliente Metalurgica del Sur SAC)
-- Nota: 'Parada P11' es compartido entre Ruta A y Ruta B
-- ------------------------------------------------------------
INSERT INTO PG_PARADERO (nombre, sede_id, activo) VALUES
    -- Ruta A
    ('Parada P01',                      2, 1),
    ('Parada P02',                      2, 1),
    ('Parada P03', 2, 1),
    ('Parada P04',                2, 1),
    ('Parada P05',                   2, 1),
    ('Parada P06',         2, 1),
    ('Parada P07',               2, 1),
    ('Parada P08',                   2, 1),
    ('Parada P09',               2, 1),
    ('Parada P10',                     2, 1),
    ('Parada P11',                         2, 1),  -- compartido Ruta A y B
    -- Ruta B (excluye Parada P11, ya insertado)
    ('Parada P12',                          2, 1),
    ('Parada P13',                    2, 1),
    ('Parada P14',                        2, 1),
    ('Parada P15',                                 2, 1),
    ('Parada P16',                                    2, 1),
    ('Parada P17',                     2, 1),
    ('Parada P18',                                  2, 1),
    ('Parada P19',          2, 1),
    ('Parada P20',      2, 1),
    ('Parada P21',     2, 1),
    ('Parada P22',                                       2, 1),
    -- Ruta C
    ('Parada P23',            2, 1),
    ('Parada P24',            2, 1),
    ('Parada P25',            2, 1),
    ('Parada P26',    2, 1),
    ('Parada P27',2, 1),
    ('Parada P28',            2, 1),
    ('Parada P29',     2, 1),
    ('Parada P30',      2, 1),
    ('Parada P31',             2, 1),
    ('Parada P32',              2, 1);
GO

-- ------------------------------------------------------------
-- PG_PARADERO — Cañete (sede_id = 3)
-- ------------------------------------------------------------
INSERT INTO PG_PARADERO (nombre, sede_id, activo) VALUES
    -- Agroindustria Costa SAC (origenes)
    ('Parada P33',    3, 1),
    ('Parada P34',      3, 1),  -- compartido con Agroexport Valle SAC
    ('Parada P35',   3, 1),
    -- Agroindustria Costa SAC (destino)
    ('Parada P36', 3, 1),
    -- Agroexport Valle SAC (origenes, excluye Parada P34 ya insertado)
    ('Parada P37',       3, 1),
    ('Parada P38',          3, 1),
    ('Parada P39',     3, 1),
    ('Parada P40',       3, 1),
    ('Parada P41',         3, 1),
    ('Parada P42',          3, 1),
    ('Parada P43', 3, 1),
    ('Parada P44',         3, 1),
    ('Parada P45',        3, 1),
    ('Parada P46',      3, 1),
    -- Agroexport Valle SAC (destinos)
    ('Parada P47',              3, 1),
    ('Parada P48',         3, 1),
    ('Parada P49',      3, 1),
    ('Parada P50',           3, 1),
    ('Parada P51',            3, 1),
    ('Parada P52',        3, 1);
GO

-- ------------------------------------------------------------
-- PG_RUTA — Pisco (sede_id=2)
-- cliente_id: Metalurgica del Sur SAC=4, Procesos Quimicos SAC=11, Corporativo Premium SAC=12
-- origen_fijo=1 rutas fijas | origen_fijo=0 rutas variables
-- calcula_llegada=0 (Tipo B ingresa hora fin manual)
-- ------------------------------------------------------------
INSERT INTO PG_RUTA (nombre, sede_id, cliente_id, origen_fijo, origen_texto, destino_texto, calcula_llegada, requiere_dos_conductores, tipo_servicio, activa) VALUES
    ('RUTA PREMIUM',  2, 12, 1, 'Origen Premium',     'Destino Premium',     0, 0, 'PERSONAL', 1),
    ('Procesos Quimicos SAC',   2, 11, 1, 'Origen Quimicos', 'Destino Quimicos', 0, 0, 'PERSONAL', 1);
GO

INSERT INTO PG_RUTA (nombre, sede_id, cliente_id, origen_fijo, destino_texto, calcula_llegada, requiere_dos_conductores, tipo_servicio, activa) VALUES
    ('Ruta A', 2, 4, 0, 'Planta Cliente Sur', 0, 0, 'PERSONAL', 1),
    ('Ruta B', 2, 4, 0, 'Planta Cliente Sur', 0, 0, 'PERSONAL', 1),
    ('Ruta C', 2, 4, 0, 'Planta Cliente Sur', 0, 0, 'PERSONAL', 1);
GO

-- ------------------------------------------------------------
-- PG_RUTA_PARADERO — Pisco rutas variables
-- IDs de paradero según orden de INSERT anterior:
--   Ruta A (ruta_id=3): paraderos 1-11
--   Ruta B (ruta_id=4): paraderos 12-22 + 11 (Parada P11)
--   Ruta C (ruta_id=5): paraderos 23-32
-- ⚠️  Verificar IDs con SELECT * FROM PG_PARADERO antes de ejecutar
-- ------------------------------------------------------------

-- Ruta A
INSERT INTO PG_RUTA_PARADERO (ruta_id, paradero_id, orden) VALUES
    (3,  1,  1), (3,  2,  2), (3,  3,  3), (3,  4,  4),
    (3,  5,  5), (3,  6,  6), (3,  7,  7), (3,  8,  8),
    (3,  9,  9), (3, 10, 10), (3, 11, 11);

-- Ruta B
INSERT INTO PG_RUTA_PARADERO (ruta_id, paradero_id, orden) VALUES
    (4, 12,  1), (4, 13,  2), (4, 14,  3), (4, 15,  4),
    (4, 16,  5), (4, 17,  6), (4, 18,  7), (4, 19,  8),
    (4, 20,  9), (4, 21, 10), (4, 22, 11), (4, 11, 12);

-- Ruta C
INSERT INTO PG_RUTA_PARADERO (ruta_id, paradero_id, orden) VALUES
    (5, 23,  1), (5, 24,  2), (5, 25,  3), (5, 26,  4),
    (5, 27,  5), (5, 28,  6), (5, 29,  7), (5, 30,  8),
    (5, 31,  9), (5, 32, 10);
GO

-- ------------------------------------------------------------
-- PG_RUTA — Cañete (sede_id=3)
-- cliente_id: Agroindustria Costa SAC=13, Agroexport Valle SAC=14
-- IDs de paradero Cañete según INSERT anterior:
--   33=Parada P33, 34=Parada P34, 35=Parada P35
--   36=Parada P36
-- ------------------------------------------------------------
INSERT INTO PG_RUTA (nombre, sede_id, cliente_id, origen_fijo, paradero_origen_id, paradero_destino_id, calcula_llegada, requiere_dos_conductores, tipo_servicio, activa) VALUES
    ('Parada P33 → Parada P36', 3, 13, 1, 33, 36, 0, 0, 'PERSONAL', 1),
    ('Parada P34 → Parada P36',   3, 13, 1, 34, 36, 0, 0, 'PERSONAL', 1),
    ('Parada P35 → Parada P36',3, 13, 1, 35, 36, 0, 0, 'PERSONAL', 1);
GO

-- ------------------------------------------------------------
-- PG_RUTA -- Canete Agroexport Valle SAC (sede_id=3, cliente_id=14)
-- 66 combinaciones validas: 11 origenes x 6 destinos
-- tiempo_estimado_min=NULL (Tipo C ingresa hora inicio y fin manual)
-- Paradero IDs: verificar con SELECT * FROM PG_PARADERO
-- ------------------------------------------------------------
INSERT INTO PG_RUTA (nombre, sede_id, cliente_id, origen_fijo, paradero_origen_id, paradero_destino_id, tiempo_estimado_min, calcula_llegada, requiere_dos_conductores, tipo_servicio, activa) VALUES
    ('Parada P34 -> Parada P47', 3, 14, 1, 34, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P34 -> Parada P48', 3, 14, 1, 34, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P34 -> Parada P49', 3, 14, 1, 34, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P34 -> Parada P50', 3, 14, 1, 34, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P34 -> Parada P51', 3, 14, 1, 34, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P34 -> Parada P52', 3, 14, 1, 34, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P37 -> Parada P47', 3, 14, 1, 37, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P37 -> Parada P48', 3, 14, 1, 37, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P37 -> Parada P49', 3, 14, 1, 37, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P37 -> Parada P50', 3, 14, 1, 37, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P37 -> Parada P51', 3, 14, 1, 37, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P37 -> Parada P52', 3, 14, 1, 37, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P38 -> Parada P47', 3, 14, 1, 38, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P38 -> Parada P48', 3, 14, 1, 38, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P38 -> Parada P49', 3, 14, 1, 38, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P38 -> Parada P50', 3, 14, 1, 38, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P38 -> Parada P51', 3, 14, 1, 38, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P38 -> Parada P52', 3, 14, 1, 38, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P39 -> Parada P47', 3, 14, 1, 39, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P39 -> Parada P48', 3, 14, 1, 39, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P39 -> Parada P49', 3, 14, 1, 39, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P39 -> Parada P50', 3, 14, 1, 39, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P39 -> Parada P51', 3, 14, 1, 39, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P39 -> Parada P52', 3, 14, 1, 39, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P40 -> Parada P47', 3, 14, 1, 40, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P40 -> Parada P48', 3, 14, 1, 40, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P40 -> Parada P49', 3, 14, 1, 40, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P40 -> Parada P50', 3, 14, 1, 40, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P40 -> Parada P51', 3, 14, 1, 40, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P40 -> Parada P52', 3, 14, 1, 40, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P41 -> Parada P47', 3, 14, 1, 41, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P41 -> Parada P48', 3, 14, 1, 41, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P41 -> Parada P49', 3, 14, 1, 41, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P41 -> Parada P50', 3, 14, 1, 41, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P41 -> Parada P51', 3, 14, 1, 41, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P41 -> Parada P52', 3, 14, 1, 41, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P42 -> Parada P47', 3, 14, 1, 42, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P42 -> Parada P48', 3, 14, 1, 42, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P42 -> Parada P49', 3, 14, 1, 42, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P42 -> Parada P50', 3, 14, 1, 42, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P42 -> Parada P51', 3, 14, 1, 42, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P42 -> Parada P52', 3, 14, 1, 42, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P43 -> Parada P47', 3, 14, 1, 43, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P43 -> Parada P48', 3, 14, 1, 43, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P43 -> Parada P49', 3, 14, 1, 43, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P43 -> Parada P50', 3, 14, 1, 43, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P43 -> Parada P51', 3, 14, 1, 43, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P43 -> Parada P52', 3, 14, 1, 43, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P44 -> Parada P47', 3, 14, 1, 44, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P44 -> Parada P48', 3, 14, 1, 44, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P44 -> Parada P49', 3, 14, 1, 44, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P44 -> Parada P50', 3, 14, 1, 44, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P44 -> Parada P51', 3, 14, 1, 44, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P44 -> Parada P52', 3, 14, 1, 44, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P45 -> Parada P47', 3, 14, 1, 45, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P45 -> Parada P48', 3, 14, 1, 45, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P45 -> Parada P49', 3, 14, 1, 45, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P45 -> Parada P50', 3, 14, 1, 45, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P45 -> Parada P51', 3, 14, 1, 45, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P45 -> Parada P52', 3, 14, 1, 45, 52, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P46 -> Parada P47', 3, 14, 1, 46, 47, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P46 -> Parada P48', 3, 14, 1, 46, 48, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P46 -> Parada P49', 3, 14, 1, 46, 49, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P46 -> Parada P50', 3, 14, 1, 46, 50, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P46 -> Parada P51', 3, 14, 1, 46, 51, NULL, 0, 0, 'PERSONAL', 1),
    ('Parada P46 -> Parada P52', 3, 14, 1, 46, 52, NULL, 0, 0, 'PERSONAL', 1);
GO


-- ------------------------------------------------------------
-- PG_RUTA -- Lima (sede_id=1), Tipo A
-- calcula_llegada=1: hora llegada = hora_inicio + tiempo_estimado_min
-- tiempo_estimado_min calculado del promedio historico (PROGRAMACION ABRIL 2026.xlsx)
-- Pendiente: Minera Altiplano SAC (2 rutas) y Minera Cordillera SAC (1 ruta): ver INSERT de mina mas abajo
-- ------------------------------------------------------------
INSERT INTO PG_RUTA (nombre, sede_id, cliente_id, origen_fijo, paradero_origen_id, paradero_destino_id, tiempo_estimado_min, calcula_llegada, requiere_dos_conductores, tipo_servicio, activa) VALUES
    ('PUENTE PIEDRA', 1, 4, 1, NULL, NULL, 160, 1, 0, 'PERSONAL', 1),
    ('ADUANAS', 1, 2, 1, NULL, NULL, 105, 1, 0, 'PERSONAL', 1),
    ('ATOCONGO', 1, 2, 1, NULL, NULL, 90, 1, 0, 'PERSONAL', 1),
    ('CALLAO', 1, 2, 1, NULL, NULL, 105, 1, 0, 'PERSONAL', 1),
    ('OLIVOS', 1, 2, 1, NULL, NULL, 95, 1, 0, 'PERSONAL', 1),
    ('PASCANA', 1, 2, 1, NULL, NULL, 125, 1, 0, 'PERSONAL', 1),
    ('PUENTE PIEDRA', 1, 2, 1, NULL, NULL, 128, 1, 0, 'PERSONAL', 1),
    ('SANTA ANITA', 1, 2, 1, NULL, NULL, 75, 1, 0, 'PERSONAL', 1),
    ('SANTA CLARA', 1, 2, 1, NULL, NULL, 102, 1, 0, 'PERSONAL', 1),
    ('SJL', 1, 2, 1, NULL, NULL, 110, 1, 0, 'PERSONAL', 1),
    ('1 de PRO', 1, 3, 1, NULL, NULL, 110, 1, 0, 'PERSONAL', 1),
    ('CALLAO FAUCETT', 1, 3, 1, NULL, NULL, 80, 1, 0, 'PERSONAL', 1),
    ('IZAGUIRRE BANCOS', 1, 3, 1, NULL, NULL, 108, 1, 0, 'PERSONAL', 1),
    ('RUTA 2 - IZAGUIRRE', 1, 3, 1, NULL, NULL, 150, 1, 0, 'PERSONAL', 1),
    ('VILLASOL', 1, 3, 1, NULL, NULL, 110, 1, 0, 'PERSONAL', 1),
    ('COMAS', 1, 5, 1, NULL, NULL, 100, 1, 0, 'PERSONAL', 1),
    ('VMT', 1, 5, 1, NULL, NULL, 55, 1, 0, 'PERSONAL', 1),
    ('CAQUETA', 1, 6, 1, NULL, NULL, 82, 1, 0, 'PERSONAL', 1),
    ('NVA. ESPERANZA - CHILCA 1 y 2', 1, 6, 1, NULL, NULL, 95, 1, 0, 'PERSONAL', 1),
    ('PACHACAMAC', 1, 6, 1, NULL, NULL, 25, 1, 0, 'PERSONAL', 1),
    ('PTE. BENAVIDES - CHILCA 1', 1, 6, 1, NULL, NULL, 60, 1, 0, 'PERSONAL', 1),
    ('PTE. BENAVIDES - CHILCA 1 y 2', 1, 6, 1, NULL, NULL, 106, 1, 0, 'PERSONAL', 1),
    ('SAN BARTOLO', 1, 6, 1, NULL, NULL, 38, 1, 0, 'PERSONAL', 1),
    ('SJM', 1, 6, 1, NULL, NULL, 100, 1, 0, 'PERSONAL', 1),
    ('FAUCETT', 1, 1, 1, NULL, NULL, 105, 1, 0, 'PERSONAL', 1),
    ('FAUCETT ADM.', 1, 1, 1, NULL, NULL, 80, 1, 0, 'PERSONAL', 1),
    ('JOSE GALVEZ', 1, 1, 1, NULL, NULL, 50, 1, 0, 'PERSONAL', 1),
    ('MANCHAY', 1, 1, 1, NULL, NULL, 75, 1, 0, 'PERSONAL', 1),
    ('PUCUSANA', 1, 1, 1, NULL, NULL, 55, 1, 0, 'PERSONAL', 1),
    ('PUENTE PIEDRA', 1, 1, 1, NULL, NULL, 104, 1, 0, 'PERSONAL', 1),
    ('PUENTE PIEDRA ADM.', 1, 1, 1, NULL, NULL, 85, 1, 0, 'PERSONAL', 1),
    ('SJL', 1, 1, 1, NULL, NULL, 97, 1, 0, 'PERSONAL', 1),
    ('SJL ADM.', 1, 1, 1, NULL, NULL, 80, 1, 0, 'PERSONAL', 1),
    ('VMT', 1, 1, 1, NULL, NULL, 78, 1, 0, 'PERSONAL', 1);
GO

-- ------------------------------------------------------------
-- PG_RUTA -- Lima rutas de mina (sede_id=1)
-- requiere_dos_conductores=1: trayectos de 10+ horas
-- tiempo_estimado_min=NULL: confirmar con area de operaciones
-- Pendiente: nombres especificos de ruta (destino exacto de mina)
-- ------------------------------------------------------------
INSERT INTO PG_RUTA (nombre, sede_id, cliente_id, origen_fijo, paradero_origen_id, paradero_destino_id, tiempo_estimado_min, calcula_llegada, requiere_dos_conductores, tipo_servicio, activa) VALUES
    ('RUTA MINA 1', 1, 7, 1, NULL, NULL, NULL, 1, 1, 'MINAS', 1),
    ('RUTA MINA 2', 1, 7, 1, NULL, NULL, NULL, 1, 1, 'MINAS', 1),
    ('CORONA',              1, 8, 1, NULL, NULL, NULL, 1, 1, 'MINAS', 1);
GO


-- ------------------------------------------------------------
-- PG_VEHICULO (flota completa — 299 unidades)
-- sede_id NULL = sede no configurada aún en piloto
-- ⚠️  Al incorporar nuevas sedes actualizar sede_id correspondiente
-- ------------------------------------------------------------
INSERT INTO PG_VEHICULO (placa, marca, modelo, anio, tipo, categoria, color, sede_id, operativo) VALUES
    ('DEM-001', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 0),
    ('DEM-002', 'MERCEDES', '1728', 2006, 'CISTERNA', 'CISTERNA FURGON', 'BLANCO', 1, 0),
    ('DEM-003', 'MAXUS', 'V-80', 2012, 'VAN', 'VAN', 'PLOMO', NULL, 0),
    ('DEM-004', 'MERCEDES', 'ACTROS 3344', 2013, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 1),
    ('DEM-005', 'MAXUS', 'V-80', 2012, 'VAN', 'VAN', 'PLOMO', NULL, 0),
    ('DEM-006', 'MERCEDES', 'ACTROS 3344', 2013, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 1),
    ('DEM-007', 'MAXUS', 'V-80', 2016, 'VAN', 'VAN', 'BLANCO', NULL, 0),
    ('DEM-008', 'MERCEDES', 'ACTROS 3344', 2013, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 0),
    ('DEM-009', 'MAXUS', 'V-80', 2012, 'VAN', 'VAN', 'PLOMO', NULL, 0),
    ('DEM-010', 'MERCEDES', 'ACTROS 3344', 2013, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 1),
    ('DEM-011', 'MAXUS', 'V-80', 2013, 'VAN', 'VAN', 'BLANCO', NULL, 0),
    ('DEM-012', 'MERCEDES', 'AXOR 2041 LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-013', 'MERCEDES', 'O-371', 2005, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 0),
    ('DEM-014', 'MERCEDES', 'AXOR 2041 LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 0),
    ('DEM-015', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-016', 'MERCEDES', 'AXOR 2041 LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 0),
    ('DEM-017', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-018', 'MERCEDES', 'AXOR 2041 LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-019', 'MERCEDES', 'O-371', 1994, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-020', 'MERCEDES', 'ACTROS 4144', 2019, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 0),
    ('DEM-021', 'MERCEDES', 'O-371', 1993, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-022', 'MERCEDES', 'ACTROS 4144', 2019, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 1),
    ('DEM-023', 'MERCEDES', 'OF-1115', 1992, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-024', 'MERCEDES', 'ACTROS 4144', NULL, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 1),
    ('DEM-025', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-026', 'MERCEDES', 'ACTROS 4144', 2019, 'VOLQUETE', 'VOLQUETE', 'AMARILLO', NULL, 0),
    ('DEM-027', 'MERCEDES', 'O-371', 1994, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-028', 'MERCEDES', 'ACTROS 2651LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-029', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 0),
    ('DEM-030', 'MERCEDES', 'ACTROS 2651LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-031', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-032', 'MERCEDES', 'ACTROS 2651LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'ROJO', NULL, 1),
    ('DEM-033', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-034', 'MERCEDES', 'O500 M', 2015, 'BUS', 'BUS INTER URBANO', 'PLOMO', 2, 0),
    ('DEM-035', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-036', 'JR GROUP', 'CARRETA', 2014, 'FURGON', 'CARRETA', 'BLANCO', NULL, 0),
    ('DEM-037', 'MERCEDES', 'OH-1622', 2012, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-038', 'JR GROUP', 'CARRETA', 2014, 'FURGON', 'CARRETA', 'BLANCO', NULL, 0),
    ('DEM-039', 'MERCEDES', 'O500 M', 2015, 'BUS', 'BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-040', 'MERCEDES', 'AXOR 2041 LS', 2019, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-041', 'MERCEDES', 'O500 R', 2012, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-042', 'MERCEDES', 'AROCS 4151K', 2020, 'VOLQUETE', 'VOLQUETE', 'NARANJA', NULL, 1),
    ('DEM-043', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-044', 'MERCEDES', 'AROCS 4151K', 2020, 'VOLQUETE', 'VOLQUETE', 'NARANJA', NULL, 0),
    ('DEM-045', 'MERCEDES', 'AROCS 4151K', 2020, 'VOLQUETE', 'VOLQUETE', 'NARANJA', NULL, 1),
    ('DEM-046', 'MERCEDES', 'AROCS 4151K', 2020, 'VOLQUETE', 'VOLQUETE', 'NARANJA', NULL, 0),
    ('DEM-047', 'SHINERAY', 'SHINERAY', 2012, 'MINIVAN', 'VAN', 'BLANCO', 1, 0),
    ('DEM-048', 'MERCEDES', 'AROCS 4151K', 2020, 'VOLQUETE', 'VOLQUETE', 'NARANJA', NULL, 1),
    ('DEM-049', 'MERCEDES', 'AROCS 4151K', 2020, 'VOLQUETE', 'VOLQUETE', 'NARANJA', NULL, 0),
    ('DEM-050', 'RMB SATECI', 'SP40', 2022, 'CARRETA', 'CARRETA', 'AMARILLO', NULL, 1),
    ('DEM-051', 'MERCEDES', 'O500 RS', 2018, 'BUS', 'BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-052', 'RMB SATECI', 'SP40', 2022, 'CARRETA', 'CARRETA', 'AMARILLO', NULL, 1),
    ('DEM-053', 'RMB SATECI', 'SP40', 2022, 'CARRETA', 'CARRETA', 'AMARILLO', NULL, 1),
    ('DEM-054', 'MERCEDES', 'O500 R', 2005, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-055', 'RMB SATECI', 'SP40', 2022, 'CARRETA', 'CARRETA', 'AMARILLO', NULL, 1),
    ('DEM-056', 'MERCEDES', 'O500 M', 2015, 'BUS', 'BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-057', 'RMB SATECI', 'SP40', 2022, 'CARRETA', 'CARRETA', 'AMARILLO', NULL, 1),
    ('DEM-058', 'RMB SATECI', 'SP40', 2022, 'CARRETA', 'CARRETA', 'AMARILLO', NULL, 1),
    ('DEM-059', 'MERCEDES', 'LO-916', 2018, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-060', 'RMB SATECI', 'SPE', 2022, 'CARRETA', 'CARRETA', 'AMARILLO', NULL, 1),
    ('DEM-061', 'MERCEDES', 'LO-916', 2018, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-062', 'MITSUBISHI', 'CANTER TURBO', 2007, 'CISTERNA', 'CISTERNA FURGON', 'BLANCO', NULL, 1),
    ('DEM-063', 'MERCEDES', 'OH-1521', 2007, 'BUS', 'BUS INTER URBANO', 'AZUL', 3, 0),
    ('DEM-064', 'MERCEDES', 'O500 M', 2015, 'BUS', 'BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-065', 'MERCEDES', 'O500 M', 2015, 'BUS', 'BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-066', 'MERCEDES', 'O500 M', 2015, 'BUS', 'BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-067', 'MAXUS', 'V-80', 2016, 'VAN', 'VAN', 'BLANCO', 2, 1),
    ('DEM-068', 'MAXUS', 'V-80', 2016, 'VAN', 'VAN', 'BLANCO', 2, 0),
    ('DEM-069', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-070', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-071', 'MERCEDES', 'LO-915', 2011, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-072', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 0),
    ('DEM-073', 'SHINERAY', 'SHINERAY', 2012, 'MINIVAN', 'VAN', 'BLANCO', 1, 1),
    ('DEM-074', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-075', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-076', 'MERCEDES', 'OF-1730', 2010, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 0),
    ('DEM-077', 'MAXUS', 'V-80', 2015, 'VAN', 'VAN', 'BLANCO', 1, 1),
    ('DEM-078', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-079', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-080', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-081', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-082', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', NULL, 0),
    ('DEM-083', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 0),
    ('DEM-084', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-085', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-086', 'MERCEDES', 'O500 R', 2011, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-087', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-088', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 1),
    ('DEM-089', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 1),
    ('DEM-090', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 0),
    ('DEM-091', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 1),
    ('DEM-092', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 1),
    ('DEM-093', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 0),
    ('DEM-094', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-095', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-096', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-097', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', 2, 1),
    ('DEM-098', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-099', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-100', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-101', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-102', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-103', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 3, 1),
    ('DEM-104', 'MERCEDES', 'OH-1622', 2012, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-105', 'MERCEDES', 'OF-1722', 2009, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-106', 'MERCEDES', 'SPRINTER 515', 2019, 'VAN', 'SPRINTER', 'BLANCO', NULL, 0),
    ('DEM-107', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', NULL, 1),
    ('DEM-108', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-109', 'MERCEDES', 'O500 R', 2007, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 0),
    ('DEM-110', 'MERCEDES', 'O500 R', 2008, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-111', 'MERCEDES', 'O500 R', 2008, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 0),
    ('DEM-112', 'MERCEDES', 'OH-1521', 2007, 'BUS', 'BUS INTER URBANO', 'AZUL', 3, 1),
    ('DEM-113', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'AZUL', 3, 1),
    ('DEM-114', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-115', 'MERCEDES', 'OF 1721', 2006, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-116', 'MERCEDES', 'O500 R', 2011, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-117', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', NULL, 1),
    ('DEM-118', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 1),
    ('DEM-119', 'MERCEDES', 'OF 1721', 2009, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-120', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-121', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-122', 'MERCEDES', 'OF 1721', 2005, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-123', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-124', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-125', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-126', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-127', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-128', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 0),
    ('DEM-129', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-130', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 3, 1),
    ('DEM-131', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 0),
    ('DEM-132', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-133', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-134', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 0),
    ('DEM-135', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-136', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-137', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-138', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-139', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-140', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-141', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-142', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-143', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-144', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-145', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-146', 'MERCEDES', 'SPRINTER 515', 2019, 'VAN', 'SPRINTER', 'BLANCO', 1, 0),
    ('DEM-147', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', NULL, 1),
    ('DEM-148', 'MERCEDES', 'SPRINTER 516', 2021, 'VAN', 'SPRINTER', 'BLANCO', NULL, 0),
    ('DEM-149', 'MERCEDES', 'LO-916', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-150', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 0),
    ('DEM-151', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-152', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-153', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 0),
    ('DEM-154', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-155', 'MERCEDES', 'OF-1722', 2009, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-156', 'MAXUS', 'V-80', 2016, 'VAN', 'VAN', 'BLANCO', NULL, 0),
    ('DEM-157', 'MERCEDES', 'OF-1318', 1995, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 0),
    ('DEM-158', 'VOLSWAGEN', '17210', 2005, 'BUS', 'BUS INTER URBANO', 'PLOMO', 3, 1),
    ('DEM-159', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-160', 'MERCEDES', 'OF 1721', 2005, 'BUS', 'BUS URBANO', 'AZUL', 3, 0),
    ('DEM-161', 'MERCEDES', 'OF 1721', 2006, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-162', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-163', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-164', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-165', 'MAXUS', 'V-80', 2012, 'VAN', 'VAN', 'PLOMO', 1, 0),
    ('DEM-166', 'MAXUS', 'V-80', 2019, 'VAN', 'VAN', 'BLANCO', 1, 1),
    ('DEM-167', 'MAXUS', 'V-80', 2019, 'VAN', 'VAN', 'BLANCO', 1, 1),
    ('DEM-168', 'MAXUS', 'V-80', 2019, 'VAN', 'VAN', 'BLANCO', 1, 1),
    ('DEM-169', 'MERCEDES', 'LO-915', 2011, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-170', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-171', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-172', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-173', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', 2, 0),
    ('DEM-174', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-175', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', 2, 0),
    ('DEM-176', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-177', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 1),
    ('DEM-178', 'JR GROUP', 'CARRETA', 2014, 'FURGON', 'CARRETA', 'BLANCO', NULL, 1),
    ('DEM-179', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-180', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-181', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', NULL, 1),
    ('DEM-182', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 1),
    ('DEM-183', 'MERCEDES', 'O500 R', 2007, 'BUS', 'BUS INTER URBANO', 'AZUL', 3, 0),
    ('DEM-184', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', NULL, 1),
    ('DEM-185', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', NULL, 0),
    ('DEM-186', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', NULL, 0),
    ('DEM-187', 'MERCEDES', 'O500 R', 2010, 'BUS', 'BUS INTER URBANO', 'AZUL', NULL, 0),
    ('DEM-188', 'MERCEDES', 'OF 1721', 2006, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-189', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-190', 'MERCEDES', 'OF-1730', 2013, 'BUS', 'BUS INTER URBANO', 'AZUL', 3, 1),
    ('DEM-191', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', 3, 1),
    ('DEM-192', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-193', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-194', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-195', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', NULL, 1),
    ('DEM-196', 'MERCEDES', 'LO-915', 2007, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-197', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-198', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-199', 'MAXUS', 'V-80', 2019, 'VAN', 'VAN', 'BLANCO', NULL, 0),
    ('DEM-200', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-201', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', 2, 1),
    ('DEM-202', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-203', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', 3, 1),
    ('DEM-204', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', 1, 0),
    ('DEM-205', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', 1, 1),
    ('DEM-206', 'MAXUS', 'V-80', 2012, 'VAN', 'VAN', 'PLOMO', 2, 0),
    ('DEM-207', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'PLOMO', 1, 1),
    ('DEM-208', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-209', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-210', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-211', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-212', 'IVECO', '170S28', 2022, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-213', 'MAXUS', 'V-80', 2019, 'VAN', 'VAN', 'PLOMO', NULL, 1),
    ('DEM-214', 'IVECO', '170S28', 2022, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-215', 'MERCEDES', 'OF 1721 E5', 2019, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-216', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', NULL, 1),
    ('DEM-217', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-218', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', 1, 0),
    ('DEM-219', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', 1, 1),
    ('DEM-220', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', NULL, 1),
    ('DEM-221', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', NULL, 1),
    ('DEM-222', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', 1, 0),
    ('DEM-223', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', 1, 0),
    ('DEM-224', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', 2, 0),
    ('DEM-225', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', 1, 0),
    ('DEM-226', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', NULL, 1),
    ('DEM-227', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', NULL, 1),
    ('DEM-228', 'MAXUS', 'V-80', 2020, 'VAN', 'VAN', 'BLANCO', NULL, 1),
    ('DEM-229', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', NULL, 1),
    ('DEM-230', 'IVECO', '170S28', 2022, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-231', 'IVECO', '170S28', 2022, 'BUS', 'BUS URBANO', 'AZUL', NULL, 0),
    ('DEM-232', 'IVECO', '170S28', 2022, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-233', 'IVECO', '170S28', 2022, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-234', 'MAXUS', 'T-60', 2021, 'CAMIONETA', 'CAMIONETA', 'BLANCO', 1, 0),
    ('DEM-235', 'MERCEDES', 'SPRINTER 515', 2019, 'VAN', 'SPRINTER', 'BLANCO', 1, 0),
    ('DEM-236', 'MERCEDES', 'SPRINTER 515', 2019, 'VAN', 'SPRINTER', 'BLANCO', 1, 0),
    ('DEM-237', 'MERCEDES', 'SPRINTER 516', 2021, 'VAN', 'SPRINTER', 'BLANCO', NULL, 1),
    ('DEM-238', 'MERCEDES', 'SPRINTER 516', 2021, 'VAN', 'SPRINTER', 'BLANCO', NULL, 1),
    ('DEM-239', 'MERCEDES', 'OF-1730', 2021, 'BUS', 'BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-240', 'MERCEDES', 'SPRINTER 516', 2021, 'VAN', 'SPRINTER', 'BLANCO', NULL, 0),
    ('DEM-241', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 0),
    ('DEM-242', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-243', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-244', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-245', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-246', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-247', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 0),
    ('DEM-248', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-249', 'MERCEDES', 'OF-1730', 2021, 'BUS', 'BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-250', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-251', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-252', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-253', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-254', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-255', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-256', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-257', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-258', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'AZUL', NULL, 1),
    ('DEM-259', 'IVECO', '150S21', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-260', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-261', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', 3, 1),
    ('DEM-262', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-263', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', 3, 1),
    ('DEM-264', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', 3, 1),
    ('DEM-265', 'MERCEDES', 'OF-914', 2017, 'MINIBUS', 'MINI BUS URBANO', 'AMARILLO Y VERDE', 3, 1),
    ('DEM-266', 'MERCEDES', 'O500 R', 2007, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-267', 'MERCEDES', 'OF-1730', 2014, 'BUS', 'BUS INTER URBANO', 'AZUL', 1, 1),
    ('DEM-268', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', 3, 1),
    ('DEM-269', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', NULL, 1),
    ('DEM-270', 'MERCEDES', 'OF 1721', 2008, 'BUS', 'BUS URBANO', 'BLANCO', 3, 1),
    ('DEM-271', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', 3, 1),
    ('DEM-272', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 0),
    ('DEM-273', 'MAXUS', 'T-60', 2020, 'CAMIONETA', 'CAMIONETA', 'BLANCO', NULL, 1),
    ('DEM-274', 'MERCEDES', 'OF-914', 2019, 'MINIBUS', 'MINI BUS INTER URBANO', 'BLANCO', NULL, 1),
    ('DEM-275', 'MERCEDES', 'OF-917', 2021, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', NULL, 1),
    ('DEM-276', 'MERCEDES', 'OF-1730 ES', 2022, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-277', 'MERCEDES', 'OF-1730 ES', 2022, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-278', 'MERCEDES', 'OF-1730 ES', 2022, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-279', 'MERCEDES', 'OF-1730 ES', 2022, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-280', 'MERCEDES', 'OF-1730 ES', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-281', 'MERCEDES', 'OF-1730 ES', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-282', 'MERCEDES', 'OF-1730 ES', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-283', 'MERCEDES', 'OF-1730 ES', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-284', 'MERCEDES', 'OF-1730 ES', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-285', 'MERCEDES', 'OF-1730 ES', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-286', 'MERCEDES', 'OF-1730 ES', 2023, 'BUS', 'BUS URBANO', 'PLOMO', NULL, 1),
    ('DEM-287', 'MAXUS', 'T-60', 2025, 'CAMIONETA', 'CAMIONETA', 'PLOMO', NULL, 0),
    ('DEM-288', 'MERCEDES', 'LO 916/24', 2025, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-289', 'MERCEDES', 'LO 916/24', 2025, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 1),
    ('DEM-290', 'MERCEDES', 'LO 916/24', 2025, 'MINIBUS', 'MINI BUS INTER URBANO', 'PLOMO', 1, 0),
    ('DEM-291', 'MAXUS', 'T-60', 2025, 'CAMIONETA', 'CAMIONETA', 'BLANCO', 1, 1),
    ('DEM-292', 'SITRAK', 'ZZ4256V344HE1B', 2025, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-293', 'SITRAK', 'ZZ4256V344HE1B', 2025, 'REMOLCADOR', 'REMOLCADOR', 'PLATA', NULL, 1),
    ('DEM-294', 'SITRAK', 'ZZ4256V344HE1B', 2025, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-295', 'SITRAK', 'ZZ4256V344HE1B', 2025, 'REMOLCADOR', 'REMOLCADOR', 'BLANCO', NULL, 1),
    ('DEM-296', 'SITRAK', 'ZZ3316V286HE1', 2026, 'VOLQUETE', 'VOLQUETE', 'BLANCO', NULL, 1),
    ('DEM-297', 'INMETARO', 'ESTANDAR', 2025, 'REMOLCADOR', 'REMOLCADOR', NULL, NULL, 1),
    ('DEM-298', 'INMETARO', 'ESTANDAR', 2025, 'REMOLCADOR', 'REMOLCADOR', NULL, NULL, 0),
    ('DEM-299', 'MAXUS', 'V-80', 2013, 'VAN', 'VAN', 'BLANCO', 1, 0);
GO



INSERT INTO PG_RUTA (nombre, sede_id, cliente_id, origen_fijo, paradero_origen_id, paradero_destino_id, calcula_llegada, requiere_dos_conductores, tipo_servicio, activa) VALUES
    ('Parada P33 → Parada P36', 3, 13, 1, 33, 36, 0, 0, 'PERSONAL', 1),
    ('Parada P34 → Parada P36',   3, 13, 1, 34, 36, 0, 0, 'PERSONAL', 1),
    ('Parada P35 → Parada P36',3, 13, 1, 35, 36, 0, 0, 'PERSONAL', 1);




-- Contraseña: Admin123 (cámbiala después)
INSERT INTO PG_USUARIO (nombre, email, password_hash, rol, sede_id, activo)
VALUES (
    'Administrador',
    'admin@transitpro.local',
    '$2b$12$DiowQulHmNLaBhMmois2wuFqeYp0ZMAbb67y.YwFHTOP7fBRAtKHS',
    'administrador',
    1,
    1
);
GO

-- ============================================================
-- 9. PG_SEDE_LOCAL  (Fix: reemplaza locales VARCHAR csv en PG_SEDE)
-- ============================================================
-- Permite JOIN limpio con T_EMPLEADOS:
--   INNER JOIN PG_SEDE_LOCAL sl ON sl.local_id = e.emp_local_id AND sl.sede_id = :id
-- ============================================================
CREATE TABLE PG_SEDE_LOCAL (
    id       INT IDENTITY(1,1) PRIMARY KEY,
    sede_id  INT NOT NULL REFERENCES PG_SEDE(sede_id),
    local_id INT NOT NULL,
    CONSTRAINT uq_sede_local UNIQUE (sede_id, local_id)
);
GO

-- Migrar datos existentes desde PG_SEDE.locales (CSV) a PG_SEDE_LOCAL
INSERT INTO PG_SEDE_LOCAL (sede_id, local_id)
SELECT sede_id, CAST(TRIM(value) AS INT)
FROM   PG_SEDE
CROSS APPLY STRING_SPLIT(ISNULL(locales, ''), ',')
WHERE  TRIM(value) <> '';
GO

-- ============================================================
-- 10. PG_CONDUCTOR_DEMO  (solo para demo/desarrollo sin T_EMPLEADOS)
-- ============================================================
CREATE TABLE PG_CONDUCTOR_DEMO (
    emp_id           INT          PRIMARY KEY,
    nombre_completo  VARCHAR(150) NOT NULL,
    emp_licencia     VARCHAR(20)  NULL,
    emp_licencia_cat VARCHAR(10)  NULL,
    emp_telefono     VARCHAR(20)  NULL,
    sede_id          INT          NOT NULL REFERENCES PG_SEDE(sede_id),
    activo           BIT          NOT NULL DEFAULT 1
);
GO

-- ============================================================
-- Fin del script
-- ============================================================
