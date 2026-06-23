# Despliegue de la demo (link público)

Guía para publicar TransitPro en un link accesible desde cualquier dispositivo,
en **modo demo** (SQLite, sin SQL Server, sin credenciales reales).

- **Backend (FastAPI)** → Render
- **Frontend (React/Vite)** → Vercel

Ambos en plan gratuito. El backend se auto-siembra al arrancar (`demo_seed.py`),
así que no hay que cargar datos manualmente.

> ⚠️ Orden importante: primero el backend, luego el frontend, y al final
> se enlazan entre sí con dos variables de entorno.

---

## Requisito previo

Sube el proyecto a un repositorio de GitHub (si aún no está). Render y Vercel
despliegan directamente desde GitHub.

```bash
git add .
git commit -m "chore: preparar proyecto para deploy de la demo"
git push
```

---

## Paso 1 — Backend en Render

1. Entra a <https://render.com> e inicia sesión con GitHub.
2. **New** → **Blueprint** y selecciona este repositorio.
   - Render detecta el archivo `render.yaml` y crea el servicio `transitpro-api`.
3. Antes de crear, revisa las variables de entorno:
   - `DEMO_MODE` = `true` (ya viene definido)
   - `SECRET_KEY` = se genera automáticamente
   - `CORS_ORIGINS` = **déjalo vacío por ahora** (se llena en el Paso 3)
4. **Apply / Create**. El primer build tarda ~3-5 min.
5. Cuando termine, copia la URL pública, p.ej.:
   `https://transitpro-api.onrender.com`
6. Verifica que responde abriendo esa URL en el navegador: debe mostrar
   `{"status":"ok", ... "demo_mode":true}`.

> 💤 En el plan gratuito el backend "se duerme" tras ~15 min de inactividad y
> tarda ~30-50 s en despertar en la primera visita. Para una demo en vivo,
> abre el link 1 minuto antes.

---

## Paso 2 — Frontend en Vercel

1. Entra a <https://vercel.com> e inicia sesión con GitHub.
2. **Add New** → **Project** y selecciona este repositorio.
3. En **Root Directory** elige la carpeta `frontend`.
   - Framework: **Vite** (lo detecta solo, gracias a `vercel.json`).
4. En **Environment Variables** agrega:
   - `VITE_API_URL` = la URL del backend del Paso 1
     (ej. `https://transitpro-api.onrender.com`, **sin** barra final).
5. **Deploy**. Al terminar copia la URL pública, p.ej.:
   `https://transitpro.vercel.app`

---

## Paso 3 — Enlazar CORS (backend ↔ frontend)

1. Vuelve a Render → servicio `transitpro-api` → **Environment**.
2. Edita `CORS_ORIGINS` con la URL del frontend del Paso 2:
   - `CORS_ORIGINS=https://transitpro.vercel.app`
3. Guarda. Render reinicia el servicio automáticamente.

¡Listo! Abre la URL de Vercel desde cualquier dispositivo.

---

## Credenciales de la demo

| Rol           | Usuario                       | Contraseña |
|---------------|-------------------------------|------------|
| Administrador | `admin@transitpro.local`      | `Admin123` |
| Programador   | `prog.lima@transitpro.local`  | `Prog123`  |
| Programador   | `prog.pisco@transitpro.local` | `Prog123`  |
| Programador   | `prog.canete@transitpro.local`| `Prog123`  |

---

## Desarrollo local (no cambia)

Sigue funcionando igual que antes:

```bash
# Backend
DEMO_MODE=true uvicorn backend.main:app --reload --port 8001

# Frontend (otra terminal)
cd frontend && npm run dev
```

En local `VITE_API_URL` queda vacío, así que se usa el proxy de Vite
(`/api` → `localhost:8001`) definido en `vite.config.js`.

---

## Archivos involucrados en el deploy

| Archivo                          | Para qué sirve |
|----------------------------------|----------------|
| `render.yaml`                    | Blueprint del backend en Render |
| `backend/requirements-deploy.txt`| Deps del deploy (sin pyodbc ni tests) |
| `frontend/vercel.json`           | Config de Vercel + rutas SPA |
| `frontend/.env.example`          | Documenta `VITE_API_URL` |
| `frontend/src/api/client.js`     | Usa `VITE_API_URL` en producción |
