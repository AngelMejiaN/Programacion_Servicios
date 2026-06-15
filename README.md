# TransitPro ERP — Sistema de Programación de Servicios de Transporte

Aplicación full-stack para la **programación y gestión diaria de servicios de transporte de personal** en empresas con flota propia y múltiples sedes. Cubre el ciclo completo: definición de rutas y paraderos, asignación de vehículos y conductores, control de estados del servicio (programado, en curso, completado), importación masiva desde Excel y notificaciones automáticas a conductores y programadores vía Telegram.

> **Nota:** Este repositorio es una versión de portafolio. El esquema de base de datos y los datos de ejemplo han sido anonimizados (nombres de clientes, placas, paraderos y credenciales son ficticios). No contiene información real de ninguna empresa.

---

## Funcionalidades principales

- **Gestión de catálogos**: sedes, clientes, vehículos (flota de ~300 unidades en el demo), rutas, paraderos y usuarios.
- **Tipos de ruta flexibles**: rutas con origen fijo, rutas variables con paraderos ordenados, y rutas de mina que exigen dos conductores.
- **Programación de servicios diarios** con cálculo de hora de llegada estimada y control de servicios que cruzan medianoche o requieren retorno.
- **Importación masiva** de programación desde una plantilla Excel.
- **Autenticación JWT** con roles (administrador, programador, supervisor) y rutas protegidas.
- **Bot de Telegram** que notifica a los conductores sus servicios del día siguiente y avisa a los programadores sobre servicios sin conductor asignado.
- **Frontend SPA** con dashboard, calendario, tema claro/oscuro y paneles de administración.

---

## Arquitectura

```
┌─────────────┐      HTTP/JSON      ┌──────────────┐      SQLAlchemy      ┌─────────────┐
│  Frontend   │ ◄─────────────────► │   Backend    │ ◄──────────────────► │ SQL Server  │
│ React + Vite│      (JWT auth)     │  FastAPI     │       (pyodbc)       │ TransitProDB│
└─────────────┘                     └──────┬───────┘                      └──────┬──────┘
                                           │                                     │
                                    ┌──────▼───────┐                             │
                                    │ Bot Telegram │ ◄───────────────────────────┘
                                    │ (aiogram)    │   lee mismos datos + notifica
                                    └──────────────┘
```

Tres componentes desacoplados que comparten la base de datos. El backend expone la API REST; el frontend la consume; el bot opera de forma autónoma sobre el mismo esquema y envía notificaciones programadas.

---

## Stack tecnológico

| Capa        | Tecnologías                                                        |
|-------------|--------------------------------------------------------------------|
| Backend     | Python, FastAPI, SQLAlchemy 2.0, Pydantic v2, python-jose (JWT), passlib/bcrypt |
| Base de datos | Microsoft SQL Server (pyodbc, ODBC Driver 17)                    |
| Frontend    | React, Vite, Tailwind CSS, Axios, React Router                     |
| Bot         | Python, Telegram Bot API                                           |
| Importación | openpyxl (plantillas Excel)                                        |

---

## Estructura del proyecto

```
.
├── backend/              API REST (FastAPI)
│   ├── models/           Modelos ORM (SQLAlchemy)
│   ├── routers/          Endpoints por recurso
│   ├── schemas/          Esquemas Pydantic (validación/serialización)
│   ├── services/         Lógica de negocio (programación, importación)
│   ├── auth.py           Hashing de contraseñas y JWT
│   └── main.py           Punto de entrada de la API
├── bot/                  Bot de Telegram (handlers, notificaciones)
├── frontend/             SPA en React + Vite
│   └── src/
│       ├── api/          Clientes HTTP por recurso
│       ├── pages/        Vistas (Dashboard, Servicios, Calendario, Admin)
│       ├── components/   Layout y componentes UI
│       └── context/      Auth y Theme (React Context)
├── schema.sql            Esquema SQL Server + datos de referencia (anonimizado)
├── plantilla_servicios_EJEMPLO.xlsx   Plantilla de importación
└── .env.example          Variables de entorno de referencia
```

---

## Puesta en marcha

### Requisitos
- Python 3.11+, Node.js 18+
- SQL Server con ODBC Driver 17

### 1. Base de datos
Crea la base `TransitProDB` y ejecuta `schema.sql` (crea tablas y carga datos de referencia).

### 2. Variables de entorno
```bash
cp .env.example .env   # completa con tus credenciales
```

### 3. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload    # docs en http://localhost:8000/docs
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

### 5. Bot (opcional)
```bash
cd bot
pip install -r requirements.txt
python -m bot.main
```

### Credenciales de demo
- Usuario: `admin@transitpro.local`
- Contraseña: `Admin123`

---

## Notas de diseño

- El sistema se integra con una tabla externa de empleados (`T_EMPLEADOS`) de solo lectura para obtener los conductores, filtrándolos por sede mediante el campo `locales`. Es un patrón habitual al construir sobre sistemas de RR.HH. existentes.
- Los servicios modelan casos reales de operación: rutas largas con dos conductores, servicios con retorno en distinta fecha (pernocte) y cruce de medianoche.
- CORS y `SECRET_KEY` están preparados para configurarse vía entorno antes de un despliegue productivo.

---

## Posibles mejoras (roadmap)

- Pruebas automatizadas (pytest + Vitest) y CI con GitHub Actions.
- Migraciones de base de datos con Alembic.
- Dockerización (docker-compose para backend, frontend y bot).
- Endpoints de reportería y exportación.
