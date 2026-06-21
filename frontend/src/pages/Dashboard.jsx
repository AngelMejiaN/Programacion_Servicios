import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { useAuth } from '../context/AuthContext'
import { getServicios } from '../api/servicios'
import {
  RefreshCw, ChevronLeft, ChevronRight,
  AlertTriangle, CheckCircle, Truck, Users,
  Building2, Search, Wrench, Bell,
  ShieldAlert, Star, MapPin, Clock, TrendingUp,
} from 'lucide-react'
import clsx from 'clsx'

// ─────────────────────────────────────────────────────────────────────────────
// Datos mock (demo — sin conexión a BD real)
// ─────────────────────────────────────────────────────────────────────────────

const SEDES_NOMBRES = ['Lima', 'Pisco', 'Cañete']

const FLOTA_SEDE = {
  Lima:   { total: 300, operativas: 270, libres: 45, mantenimiento: 30 },
  Pisco:  { total: 45,  operativas: 38,  libres: 8,  mantenimiento: 7  },
  Cañete: { total: 28,  operativas: 22,  libres: 5,  mantenimiento: 6  },
}

const PERSONAL_SEDE = {
  Lima:   { total: 52, activos: 48, rendimiento: 89 },
  Pisco:  { total: 12, activos: 10, rendimiento: 76 },
  Cañete: { total: 8,  activos: 7,  rendimiento: 83 },
}

const MTTR_SEDE = {
  Lima:   { mttr: 45, alertas: 23, resueltas: 21, tendencia: [52, 48, 41, 38, 45, 30, 0] },
  Pisco:  { mttr: 72, alertas: 8,  resueltas: 6,  tendencia: [90, 75, 68, 72, 65, 0,  0] },
  Cañete: { mttr: 58, alertas: 5,  resueltas: 5,  tendencia: [62, 55, 58, 50, 48, 0,  0] },
}

const CONDUCTORES_SEDE = {
  Lima: [
    { nombre: 'GARCIA, Carlos',   eficiencia: 94 },
    { nombre: 'TORRES, Miguel',   eficiencia: 91 },
    { nombre: 'RODRIGUEZ, Juan',  eficiencia: 88 },
    { nombre: 'LOPEZ, Pedro',     eficiencia: 85 },
    { nombre: 'FLORES, Roberto',  eficiencia: 76 },
  ],
  Pisco: [
    { nombre: 'QUISPE, Jorge',   eficiencia: 80 },
    { nombre: 'MAMANI, Víctor',  eficiencia: 78 },
    { nombre: 'HUAMAN, Luis',    eficiencia: 72 },
  ],
  Cañete: [
    { nombre: 'VARGAS, Raúl',    eficiencia: 83 },
    { nombre: 'RAMOS, Eduardo',  eficiencia: 79 },
  ],
}

const ALERTAS_MATRIZ = [
  { sede: 'Lima',   falla: 8, incumplimiento: 5, humano: 3, terceros: 7 },
  { sede: 'Pisco',  falla: 3, incumplimiento: 2, humano: 1, terceros: 2 },
  { sede: 'Cañete', falla: 2, incumplimiento: 1, humano: 0, terceros: 2 },
]

const ALERTAS_GRID_INIT = [
  { id: 'ALT-001', fechaHora: '21/06 04:12', prioridad: 'Alta',  tipo: 'Falla Mecánica',           vehiculo: 'LIM-045', cliente: 'MINERA SHOGUN',      ruta: 'CALLAO',       desc: 'Falla en sistema de frenos — unidad inmovilizada en ruta',         estado: 'Pendiente'   },
  { id: 'ALT-002', fechaHora: '21/06 05:33', prioridad: 'Alta',  tipo: 'Incumplimiento Conductor',  vehiculo: 'LIM-112', cliente: 'CONSTRUCTORA LIMA',  ruta: 'SJL',          desc: 'Conductor no se presentó al turno asignado',                       estado: 'Pendiente'   },
  { id: 'ALT-003', fechaHora: '21/06 06:47', prioridad: 'Media', tipo: 'Falla Mecánica',           vehiculo: 'LIM-223', cliente: 'AGRO EXPORT S.A.C.', ruta: 'ATE',          desc: 'Recalentamiento de motor detectado en ruta',                       estado: 'Pendiente'   },
  { id: 'ALT-004', fechaHora: '21/06 07:05', prioridad: 'Alta',  tipo: 'Error Humano',             vehiculo: 'LIM-067', cliente: 'MINERA SHOGUN',      ruta: 'CHORRILLOS',   desc: 'Ruta incorrecta — desvío de 25 min sin notificación',               estado: 'Resuelto'    },
  { id: 'ALT-005', fechaHora: '21/06 07:22', prioridad: 'Baja',  tipo: 'Error de Terceros',        vehiculo: 'LIM-189', cliente: 'NEXUS CORP',         ruta: 'LA MOLINA',    desc: 'Bloqueo de vía por obras municipales',                             estado: 'Resuelto'    },
  { id: 'ALT-006', fechaHora: '21/06 08:41', prioridad: 'Media', tipo: 'Incumplimiento Conductor', vehiculo: 'LIM-034', cliente: 'CONSTRUCTORA LIMA',  ruta: 'SURCO',        desc: 'Llegada con 35 min de retraso sin notificación previa',            estado: 'Pendiente'   },
  { id: 'ALT-007', fechaHora: '21/06 09:15', prioridad: 'Alta',  tipo: 'Falla Mecánica',           vehiculo: 'LIM-301', cliente: 'AGRO EXPORT S.A.C.', ruta: 'MIRAFLORES',  desc: 'Llanta pinchada en autopista — servicio cancelado',                estado: 'Pendiente'   },
  { id: 'ALT-008', fechaHora: '21/06 10:03', prioridad: 'Baja',  tipo: 'Error Humano',             vehiculo: 'LIM-156', cliente: 'MINERA SHOGUN',      ruta: 'RIMAC',        desc: 'Documentación de servicio incompleta',                             estado: 'Resuelto'    },
  { id: 'ALT-009', fechaHora: '21/06 11:28', prioridad: 'Media', tipo: 'Error de Terceros',        vehiculo: 'LIM-088', cliente: 'NEXUS CORP',         ruta: 'INDEPENDENCIA',desc: 'Accidente de tercero bloqueó la vía durante 45 min',               estado: 'Resuelto'    },
  { id: 'ALT-010', fechaHora: '21/06 13:45', prioridad: 'Alta',  tipo: 'Falla Mecánica',           vehiculo: 'LIM-212', cliente: 'CONSTRUCTORA LIMA',  ruta: 'CARABAYLLO',   desc: 'Falla eléctrica total — unidad remolcada a taller',                estado: 'Pendiente'   },
  { id: 'ALT-011', fechaHora: '21/06 14:20', prioridad: 'Media', tipo: 'Incumplimiento Conductor', vehiculo: 'LIM-099', cliente: 'NEXUS CORP',         ruta: 'VILLA MARIA',  desc: 'Conductor reportó enfermedad — sin reemplazo disponible',          estado: 'En gestión'  },
  { id: 'ALT-012', fechaHora: '21/06 15:10', prioridad: 'Baja',  tipo: 'Error de Terceros',        vehiculo: 'LIM-178', cliente: 'AGRO EXPORT S.A.C.', ruta: 'LOS OLIVOS',  desc: 'Cierre de puente por mantenimiento vial municipal',                estado: 'Resuelto'    },
]

const CLIENTES_MOCK = {
  'MINERA SHOGUN':      { retencion: 94, volumen_mes: 285, sla: 91.2, weekly: [47, 52, 44, 48, 45, 0, 0] },
  'CONSTRUCTORA LIMA':  { retencion: 87, volumen_mes: 198, sla: 78.5, weekly: [32, 35, 30, 33, 31, 0, 0] },
  'AGRO EXPORT S.A.C.': { retencion: 91, volumen_mes: 156, sla: 88.9, weekly: [25, 27, 24, 26, 25, 0, 0] },
  'NEXUS CORP':         { retencion: 83, volumen_mes: 124, sla: 85.3, weekly: [20, 22, 18, 21, 19, 0, 0] },
}

const DIAS_SEM = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

function hashInt(str) {
  let h = 5381
  for (let i = 0; i < str.length; i++) h = ((h * 33) ^ str.charCodeAt(i)) >>> 0
  return h
}

// ─────────────────────────────────────────────────────────────────────────────
// Primitivos de gráficos — CSS puro, sin dependencias externas
// ─────────────────────────────────────────────────────────────────────────────

function HBar({ label, value, max, colorClass, suffix = '' }) {
  const pct = max > 0 ? Math.min(Math.round(value / max * 100), 100) : 0
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-36 truncate text-gray-600 dark:text-slate-400 font-medium shrink-0" title={label}>{label}</span>
      <div className="flex-1 bg-gray-100 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all duration-500', colorClass)} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right tabular-nums text-gray-700 dark:text-slate-300 font-semibold shrink-0">
        {value}{suffix}
      </span>
    </div>
  )
}

function VBarChart({ data, colorClass = 'bg-brand-500', height = 90 }) {
  const maxVal = Math.max(...data.map(d => d.value), 1)
  return (
    <div className="flex items-end gap-0.5" style={{ height }}>
      {data.map((d, i) => {
        const barH = Math.max(Math.round((d.value / maxVal) * (height - 26)), d.value > 0 ? 3 : 0)
        return (
          <div key={i} className="flex-1 flex flex-col items-center min-w-0" style={{ height }}>
            <div className="flex-1 flex flex-col justify-end">
              {d.value > 0 && (
                <span className="text-center tabular-nums text-gray-400 dark:text-slate-500 leading-none mb-0.5" style={{ fontSize: 9 }}>
                  {d.value}
                </span>
              )}
              <div className={clsx('w-full rounded-t-sm transition-all duration-500', colorClass)} style={{ height: barH }} />
            </div>
            <span className="text-gray-400 dark:text-slate-500 truncate w-full text-center leading-none mt-1" style={{ fontSize: 9 }}>
              {d.label}
            </span>
          </div>
        )
      })}
    </div>
  )
}

function StackedBar({ rowLabel, seg }) {
  const total = seg.reduce((s, x) => s + x.v, 0) || 1
  return (
    <div className="flex items-center gap-2">
      <span className="w-14 text-xs text-gray-600 dark:text-slate-400 font-medium truncate shrink-0">{rowLabel}</span>
      <div className="flex flex-1 h-6 rounded overflow-hidden">
        {seg.map((s, i) =>
          s.v > 0 ? (
            <div
              key={i}
              className={clsx('flex items-center justify-center text-white font-bold transition-all', s.color)}
              style={{ width: `${Math.round(s.v / total * 100)}%`, fontSize: 11 }}
              title={`${s.label}: ${s.v}`}
            >
              {s.v}
            </div>
          ) : null
        )}
      </div>
      <span className="text-xs tabular-nums text-gray-400 dark:text-slate-500 w-5 text-right shrink-0">{total}</span>
    </div>
  )
}

function MiniDonut({ segments, size = 96 }) {
  let acc = 0
  const stops = segments
    .filter(s => s.pct > 0)
    .map(s => { const from = acc; acc += s.pct; return `${s.color} ${from}% ${acc}%` })
    .join(', ')
  const inner = size * 0.3
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <div className="rounded-full" style={{ width: size, height: size, background: stops ? `conic-gradient(${stops})` : '#e5e7eb' }} />
      <div className="absolute rounded-full bg-white dark:bg-slate-800" style={{ inset: inner }} />
    </div>
  )
}

function KpiCard({ label, value, sub, icon: Icon, bg, textMain, textSub, iconBg }) {
  return (
    <div className={clsx('rounded-xl p-4 flex items-start gap-3 border', bg)}>
      <div className={clsx('rounded-lg p-2 shrink-0', iconBg)}>
        <Icon size={18} className={textMain} />
      </div>
      <div className="min-w-0">
        <p className={clsx('text-2xl font-bold leading-none tabular-nums', textMain)}>{value}</p>
        <p className={clsx('text-xs font-semibold mt-1 uppercase tracking-wide', textMain, 'opacity-70')}>{label}</p>
        {sub && <p className={clsx('text-xs mt-0.5', textSub)}>{sub}</p>}
      </div>
    </div>
  )
}

function SectionTitle({ icon: Icon, title, sub }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <Icon size={15} className="text-brand-600 dark:text-brand-400 shrink-0" />
      <div>
        <p className="text-sm font-semibold text-gray-700 dark:text-slate-300">{title}</p>
        {sub && <p className="text-xs text-gray-400 dark:text-slate-500">{sub}</p>}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Pestaña: General — Resumen ejecutivo
// ─────────────────────────────────────────────────────────────────────────────

function TabGeneral({ servicios, fecha, cambiarFecha, isLoading, refetch }) {
  const esHoy = fecha === format(new Date(), 'yyyy-MM-dd')
  const fechaDisplay = format(new Date(fecha + 'T12:00:00'), "EEEE d 'de' MMMM", { locale: es })

  const m = useMemo(() => {
    const total      = servicios.length
    const prog       = servicios.filter(s => s.estado === 'PROGRAMADO').length
    const en_curso   = servicios.filter(s => s.estado === 'EN_CURSO').length
    const completado = servicios.filter(s => s.estado === 'COMPLETADO').length
    const cancelado  = servicios.filter(s => s.estado === 'CANCELADO').length

    const compConEst = servicios.filter(s => s.estado === 'COMPLETADO' && s.hora_llegada_real && s.hora_llegada_est)
    const aTiempo = compConEst.filter(s => s.hora_llegada_real <= s.hora_llegada_est).length
    const sla = compConEst.length >= 3 ? Math.round(aTiempo / compConEst.length * 100) : 92

    const vehiculosUnicos = new Set(servicios.map(s => s.vehiculo_id).filter(Boolean)).size
    const flotaPct = vehiculosUnicos ? Math.min(Math.round(vehiculosUnicos / 300 * 100), 100) : 85

    const ahoraStr = format(new Date(), 'HH:mm')
    const alertasCrit = servicios.filter(s =>
      s.estado === 'EN_CURSO' && s.hora_llegada_est &&
      s.hora_llegada_est.slice(0, 5) < ahoraStr && !s.hora_llegada_real
    ).length

    const porHora = {}
    for (const s of servicios) {
      const h = parseInt(s.hora_inicio?.slice(0, 2) ?? '0')
      porHora[h] = (porHora[h] ?? 0) + 1
    }
    const horasData = Array.from({ length: 16 }, (_, i) => ({
      label: `${i + 5}h`,
      value: porHora[i + 5] ?? 0,
    }))

    const porCliente = {}
    for (const s of servicios) {
      if (s.cliente_nombre) porCliente[s.cliente_nombre] = (porCliente[s.cliente_nombre] ?? 0) + 1
    }
    const topClientes = Object.entries(porCliente).sort((a, b) => b[1] - a[1]).slice(0, 5)
      .map(([nombre, count]) => ({ nombre, count }))

    return { total, prog, en_curso, completado, cancelado, sla, flotaPct, vehiculosUnicos, alertasCrit, horasData, topClientes }
  }, [servicios])

  const DONUT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']

  return (
    <div className="space-y-5">
      {/* Navegación de fecha */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <p className="text-sm text-gray-600 dark:text-slate-300 capitalize font-medium">{fechaDisplay}</p>
        <div className="flex items-center gap-2">
          <button onClick={() => cambiarFecha(-1)} className="btn-secondary px-2.5 py-1.5"><ChevronLeft size={15} /></button>
          <button
            onClick={() => cambiarFecha(0)}
            className={clsx('btn-secondary text-xs px-3 py-1.5', esHoy && 'bg-brand-50 dark:bg-brand-900/50 border-brand-300 dark:border-brand-700 text-brand-700 dark:text-brand-300 font-semibold')}
          >Hoy</button>
          <button onClick={() => cambiarFecha(1)} className="btn-secondary px-2.5 py-1.5"><ChevronRight size={15} /></button>
          <button onClick={refetch} className="btn-secondary px-2.5 py-1.5" title="Actualizar">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-3 gap-3">
        <KpiCard
          label="Utilización de Flota" value={`${m.flotaPct}%`}
          sub={`${m.vehiculosUnicos} unidades en servicio hoy`}
          icon={Truck}
          bg="bg-brand-50 dark:bg-brand-900/20 border-brand-100 dark:border-brand-900"
          textMain="text-brand-700 dark:text-brand-100"
          textSub="text-brand-600/70 dark:text-brand-300/70"
          iconBg="bg-brand-100 dark:bg-brand-900"
        />
        <KpiCard
          label="SLA de Puntualidad" value={`${m.sla}%`}
          sub="Llegadas a tiempo sobre completados"
          icon={CheckCircle}
          bg="bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-900"
          textMain="text-green-700 dark:text-green-300"
          textSub="text-green-600/70 dark:text-green-400/70"
          iconBg="bg-green-100 dark:bg-green-900"
        />
        <KpiCard
          label="Alertas Críticas" value={String(m.alertasCrit).padStart(2, '0')}
          sub="Servicios EN CURSO con retraso activo"
          icon={AlertTriangle}
          bg="bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-900"
          textMain="text-red-600 dark:text-red-300"
          textSub="text-red-500/70 dark:text-red-400/70"
          iconBg="bg-red-100 dark:bg-red-900"
        />
      </div>

      {/* Gráficos intermedios */}
      <div className="grid grid-cols-2 gap-4">
        <div className="card p-4">
          <SectionTitle icon={TrendingUp} title="Estado de servicios del día" sub={`${m.total} servicios totales`} />
          <div className="space-y-2.5">
            {[
              { label: 'Programados', val: m.prog,       color: 'bg-yellow-400' },
              { label: 'En curso',    val: m.en_curso,   color: 'bg-green-500'  },
              { label: 'Completados', val: m.completado, color: 'bg-blue-500'   },
              { label: 'Cancelados',  val: m.cancelado,  color: 'bg-red-400'    },
            ].map(r => <HBar key={r.label} label={r.label} value={r.val} max={m.total || 1} colorClass={r.color} />)}
          </div>
          <div className="flex h-2.5 rounded-full overflow-hidden gap-px mt-3">
            {[
              { v: m.prog,       c: 'bg-yellow-400' },
              { v: m.en_curso,   c: 'bg-green-500'  },
              { v: m.completado, c: 'bg-blue-500'   },
              { v: m.cancelado,  c: 'bg-red-400'    },
            ].map((s, i) => (
              <div key={i} className={clsx('transition-all duration-500', s.c)} style={{ width: `${m.total ? s.v / m.total * 100 : 0}%` }} />
            ))}
          </div>
        </div>

        <div className="card p-4">
          <SectionTitle icon={Clock} title="Volumen de viajes por hora" sub="Servicios iniciados por franja horaria" />
          <VBarChart data={m.horasData} colorClass="bg-brand-500 dark:bg-brand-600" height={100} />
        </div>
      </div>

      {/* Analytics macros */}
      <div className="grid grid-cols-3 gap-4">
        {/* A: Efectividad del Personal */}
        <div className="card p-4">
          <SectionTitle icon={Users} title="Efectividad del Personal" sub="Eficiencia por conductor — Lima" />
          <div className="space-y-2">
            {CONDUCTORES_SEDE.Lima.map(c => (
              <HBar key={c.nombre} label={c.nombre} value={c.eficiencia} max={100} colorClass="bg-brand-500" suffix="%" />
            ))}
          </div>
        </div>

        {/* B: Distribución de Clientes */}
        <div className="card p-4">
          <SectionTitle icon={Star} title="Distribución de Clientes" sub="Concentración de operaciones hoy" />
          {m.topClientes.length > 0 ? (
            <div className="flex gap-3 items-center">
              <MiniDonut
                segments={m.topClientes.map((c, i) => ({
                  pct: Math.round(c.count / m.total * 100),
                  color: DONUT_COLORS[i],
                }))}
                size={88}
              />
              <div className="space-y-1.5 flex-1 min-w-0">
                {m.topClientes.map((c, i) => (
                  <div key={c.nombre} className="flex items-center gap-1.5 text-xs">
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ background: DONUT_COLORS[i] }} />
                    <span className="truncate text-gray-600 dark:text-slate-400 flex-1">{c.nombre}</span>
                    <span className="font-semibold tabular-nums text-gray-700 dark:text-slate-300">{c.count}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-300 dark:text-slate-600 text-center py-6">Sin datos</p>
          )}
        </div>

        {/* C: Matriz de Alertas Mensuales */}
        <div className="card p-4">
          <SectionTitle icon={ShieldAlert} title="Alertas Mensuales por Sede" sub="Frecuencia por tipo de incidencia" />
          <div className="space-y-2">
            {ALERTAS_MATRIZ.map(row => (
              <StackedBar
                key={row.sede}
                rowLabel={row.sede}
                seg={[
                  { v: row.falla,          color: 'bg-red-500',    label: 'Falla Mecánica'    },
                  { v: row.incumplimiento, color: 'bg-orange-400', label: 'Incumplimiento'    },
                  { v: row.humano,         color: 'bg-yellow-400', label: 'Error Humano'      },
                  { v: row.terceros,       color: 'bg-gray-400',   label: 'Error de Terceros' },
                ]}
              />
            ))}
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-3">
            {[
              { c: 'bg-red-500',    l: 'Falla mec.'  },
              { c: 'bg-orange-400', l: 'Incumpl.'    },
              { c: 'bg-yellow-400', l: 'Humano'      },
              { c: 'bg-gray-400',   l: 'Terceros'    },
            ].map(x => (
              <span key={x.l} className="flex items-center gap-1 text-xs text-gray-500 dark:text-slate-400">
                <span className={clsx('w-2 h-2 rounded-sm inline-block shrink-0', x.c)} />{x.l}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Pestaña: Clientes — Filtro por cuenta corporativa
// ─────────────────────────────────────────────────────────────────────────────

function TabClientes({ servicios }) {
  const [busqueda, setBusqueda]       = useState('')
  const [showDrop, setShowDrop]       = useState(false)
  const [seleccionado, setSeleccionado] = useState(null)

  const clientes = useMemo(() => {
    const map = {}
    for (const s of servicios) {
      if (!s.cliente_nombre) continue
      if (!map[s.cliente_nombre]) map[s.cliente_nombre] = { nombre: s.cliente_nombre, count: 0, rutas: {} }
      map[s.cliente_nombre].count++
      if (s.ruta_nombre) map[s.cliente_nombre].rutas[s.ruta_nombre] = (map[s.cliente_nombre].rutas[s.ruta_nombre] ?? 0) + 1
    }
    return Object.values(map).sort((a, b) => b.count - a.count)
  }, [servicios])

  const filtrados = clientes.filter(c => c.nombre.toLowerCase().includes(busqueda.toLowerCase()))

  const selData = useMemo(() => {
    if (!seleccionado) return null
    const svs = servicios.filter(s => s.cliente_nombre === seleccionado.nombre)
    const compConEst = svs.filter(s => s.estado === 'COMPLETADO' && s.hora_llegada_real && s.hora_llegada_est)
    const slaHoy = compConEst.length >= 2
      ? Math.round(compConEst.filter(s => s.hora_llegada_real <= s.hora_llegada_est).length / compConEst.length * 100)
      : null

    const topRutas = Object.entries(seleccionado.rutas)
      .sort((a, b) => b[1] - a[1]).slice(0, 7)
      .map(([r, c]) => ({ label: r, value: c }))

    const mock = CLIENTES_MOCK[seleccionado.nombre]
    const weekly = mock
      ? DIAS_SEM.map((d, i) => ({ label: d, value: mock.weekly[i] }))
      : DIAS_SEM.map((d, i) => ({
          label: d,
          value: i < 5 ? Math.max(1, seleccionado.count + (hashInt(seleccionado.nombre + i) % 10) - 5) : 0,
        }))

    const retencion  = mock?.retencion ?? 85
    const volumenMes = mock?.volumen_mes ?? seleccionado.count * 28
    const slaFinal   = slaHoy ?? mock?.sla ?? 87

    return { svs, topRutas, weekly, retencion, volumenMes, slaFinal }
  }, [seleccionado, servicios])

  function elegir(c) {
    setSeleccionado(c)
    setBusqueda('')
    setShowDrop(false)
  }

  return (
    <div className="space-y-5">
      {/* Dropdown con buscador */}
      <div className="relative max-w-sm">
        <p className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">Cliente corporativo</p>
        <div
          className="input flex items-center gap-2 cursor-pointer"
          onClick={() => setShowDrop(v => !v)}
        >
          <Search size={14} className="text-gray-400 shrink-0" />
          <span className={seleccionado ? 'text-gray-900 dark:text-slate-100 text-sm' : 'text-gray-400 text-sm'}>
            {seleccionado?.nombre ?? 'Buscar cliente...'}
          </span>
        </div>
        {showDrop && (
          <div className="absolute z-20 mt-1 w-full bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg overflow-hidden">
            <div className="p-2 border-b border-gray-100 dark:border-slate-700">
              <input
                autoFocus
                className="input text-sm py-1.5"
                placeholder="Escribir nombre..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
                onClick={e => e.stopPropagation()}
              />
            </div>
            <ul className="max-h-52 overflow-y-auto">
              {filtrados.length === 0 && (
                <li className="px-3 py-2 text-sm text-gray-400 dark:text-slate-500">Sin resultados</li>
              )}
              {filtrados.map(c => (
                <li
                  key={c.nombre}
                  onClick={() => elegir(c)}
                  className="px-3 py-2 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-700 cursor-pointer"
                >
                  <span className="text-sm text-gray-800 dark:text-slate-200">{c.nombre}</span>
                  <span className="text-xs text-gray-400 dark:text-slate-500 tabular-nums">{c.count} serv.</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {!seleccionado ? (
        <div className="card flex flex-col items-center justify-center py-16 text-center gap-3">
          <Star size={36} className="text-gray-200 dark:text-slate-700" />
          <p className="text-sm font-medium text-gray-400 dark:text-slate-500">Selecciona un cliente para ver su análisis</p>
          <p className="text-xs text-gray-300 dark:text-slate-600">{clientes.length} clientes disponibles hoy</p>
        </div>
      ) : (
        <div className="space-y-5">
          {/* KPIs del cliente */}
          <div className="grid grid-cols-3 gap-3">
            <KpiCard
              label="Índice de Retención" value={`${selData.retencion}%`}
              sub="Fidelidad histórica del cliente"
              icon={Star}
              bg="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-100 dark:border-yellow-900"
              textMain="text-yellow-700 dark:text-yellow-300"
              textSub="text-yellow-600/70 dark:text-yellow-400/70"
              iconBg="bg-yellow-100 dark:bg-yellow-900"
            />
            <KpiCard
              label="Volumen del Mes" value={selData.volumenMes}
              sub="Servicios asignados en junio"
              icon={TrendingUp}
              bg="bg-brand-50 dark:bg-brand-900/20 border-brand-100 dark:border-brand-900"
              textMain="text-brand-700 dark:text-brand-100"
              textSub="text-brand-600/70 dark:text-brand-300/70"
              iconBg="bg-brand-100 dark:bg-brand-900"
            />
            <KpiCard
              label="SLA Puntualidad" value={`${selData.slaFinal}%`}
              sub="Llegadas a tiempo para este cliente"
              icon={CheckCircle}
              bg="bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-900"
              textMain="text-green-700 dark:text-green-300"
              textSub="text-green-600/70 dark:text-green-400/70"
              iconBg="bg-green-100 dark:bg-green-900"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Gráfico 1: Timeline semanal */}
            <div className="card p-4">
              <SectionTitle icon={TrendingUp} title="Evolución semanal de servicios" sub={`Semana actual — ${seleccionado.nombre}`} />
              <VBarChart data={selData.weekly} colorClass="bg-brand-500 dark:bg-brand-600" height={110} />
            </div>

            {/* Gráfico 2: Top rutas */}
            <div className="card p-4">
              <SectionTitle icon={MapPin} title="Top rutas y destinos" sub="Frecuencia de solicitud por ruta" />
              {selData.topRutas.length > 0 ? (
                <div className="space-y-2">
                  {selData.topRutas.map(r => (
                    <HBar
                      key={r.label} label={r.label} value={r.value}
                      max={selData.topRutas[0].value} colorClass="bg-blue-500"
                    />
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-300 dark:text-slate-600 text-center py-6">Sin rutas hoy</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Pestaña: Sedes — Análisis operativo por base
// ─────────────────────────────────────────────────────────────────────────────

function TabSedes() {
  const [sedeActiva, setSedeActiva] = useState('Lima')
  const flota    = FLOTA_SEDE[sedeActiva]
  const personal = PERSONAL_SEDE[sedeActiva]
  const mttr     = MTTR_SEDE[sedeActiva]
  const flotaPct = Math.round(flota.operativas / flota.total * 100)

  const mttrData = DIAS_SEM.map((d, i) => ({ label: d, value: mttr.tendencia[i] }))

  return (
    <div className="space-y-5">
      {/* Segmented control */}
      <div>
        <p className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-2">Sede operativa</p>
        <div className="flex gap-1 p-1 bg-gray-100 dark:bg-slate-800 rounded-xl w-fit">
          {SEDES_NOMBRES.map(s => (
            <button
              key={s}
              onClick={() => setSedeActiva(s)}
              className={clsx(
                'px-6 py-2 rounded-lg text-sm font-semibold transition-all',
                sedeActiva === s
                  ? 'bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 shadow-sm'
                  : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* KPIs de sede */}
      <div className="grid grid-cols-2 gap-4">
        {/* Flota */}
        <div className="card p-4 space-y-4">
          <SectionTitle icon={Truck} title="Disponibilidad de Flota" sub={`Base operativa — ${sedeActiva}`} />
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              { label: 'Operativas', val: flota.operativas, cls: 'text-green-600 dark:text-green-400' },
              { label: 'Libres',     val: flota.libres,     cls: 'text-blue-600 dark:text-blue-400'   },
              { label: 'Mantenim.', val: flota.mantenimiento, cls: 'text-red-500 dark:text-red-400'   },
            ].map(item => (
              <div key={item.label} className="bg-gray-50 dark:bg-slate-700/50 rounded-lg py-3">
                <p className={clsx('text-2xl font-bold tabular-nums', item.cls)}>{item.val}</p>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>
          <div>
            <div className="flex justify-between text-xs text-gray-500 dark:text-slate-400 mb-1">
              <span>Utilización total</span>
              <span className="font-semibold tabular-nums">{flotaPct}%</span>
            </div>
            <div className="h-3 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-brand-500 rounded-full transition-all duration-500" style={{ width: `${flotaPct}%` }} />
            </div>
            <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">{flota.total} unidades en flota total</p>
          </div>
        </div>

        {/* Personal */}
        <div className="card p-4 space-y-4">
          <SectionTitle icon={Users} title="Rendimiento del Personal" sub={`Conductores asignados — ${sedeActiva}`} />
          <div className="grid grid-cols-2 gap-3 text-center">
            {[
              { label: 'Activos',   val: personal.activos,              cls: 'text-green-600 dark:text-green-400' },
              { label: 'Inactivos', val: personal.total - personal.activos, cls: 'text-gray-500 dark:text-slate-400' },
            ].map(item => (
              <div key={item.label} className="bg-gray-50 dark:bg-slate-700/50 rounded-lg py-3">
                <p className={clsx('text-2xl font-bold tabular-nums', item.cls)}>{item.val}</p>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>
          <div>
            <div className="flex justify-between text-xs text-gray-500 dark:text-slate-400 mb-1">
              <span>Rendimiento promedio</span>
              <span className="font-semibold tabular-nums">{personal.rendimiento}%</span>
            </div>
            <div className="h-3 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-green-500 rounded-full transition-all duration-500" style={{ width: `${personal.rendimiento}%` }} />
            </div>
          </div>
          <div className="space-y-1.5 pt-1">
            {(CONDUCTORES_SEDE[sedeActiva] ?? []).slice(0, 3).map(c => (
              <HBar key={c.nombre} label={c.nombre} value={c.eficiencia} max={100} colorClass="bg-brand-500" suffix="%" />
            ))}
          </div>
        </div>
      </div>

      {/* MTTR */}
      <div className="card p-4 space-y-4">
        <div className="flex items-start justify-between">
          <SectionTitle icon={Clock} title={`MTTR — Tiempo Medio de Resolución`} sub={`Velocidad de la sede ${sedeActiva} para resolver alertas`} />
          <div className="flex gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-orange-500 tabular-nums">{mttr.mttr} min</p>
              <p className="text-xs text-gray-400 dark:text-slate-500">Promedio MTTR</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400 tabular-nums">{mttr.resueltas}/{mttr.alertas}</p>
              <p className="text-xs text-gray-400 dark:text-slate-500">Alertas resueltas</p>
            </div>
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-slate-400 mb-2">Tendencia semanal MTTR (minutos)</p>
          <VBarChart data={mttrData} colorClass="bg-orange-400" height={100} />
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Pestaña: Alertas — Centro de gestión de crisis
// ─────────────────────────────────────────────────────────────────────────────

const PRIORIDAD_CFG = {
  Alta:  { bg: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',    dot: 'bg-red-500'    },
  Media: { bg: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300', dot: 'bg-orange-400' },
  Baja:  { bg: 'bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300', dot: 'bg-gray-400'   },
}
const ESTADO_CFG = {
  Pendiente:    'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300',
  'En gestión': 'bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
  'En taller':  'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  Resuelto:     'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300',
}

function TabAlertas() {
  const [alertas, setAlertas] = useState(ALERTAS_GRID_INIT)
  const [toast, setToast]     = useState(null)
  const [pagina, setPagina]   = useState(0)
  const [filtroPrio, setFiltroPrio] = useState('')
  const [filtroEst, setFiltroEst]   = useState('')
  const POR_PAG = 8

  const filtradas = alertas.filter(a =>
    (!filtroPrio || a.prioridad === filtroPrio) &&
    (!filtroEst  || a.estado    === filtroEst)
  )
  const paginas = Math.ceil(filtradas.length / POR_PAG)
  const vista   = filtradas.slice(pagina * POR_PAG, (pagina + 1) * POR_PAG)

  function showToast(msg) {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  function asignarTaller(id) {
    setAlertas(a => a.map(x => x.id === id ? { ...x, estado: 'En taller' } : x))
    showToast(`${id} — asignada al taller ✓`)
  }

  function notificarOp(id) {
    showToast(`${id} — notificación enviada al operador ✓`)
  }

  const resueltas  = alertas.filter(a => a.estado === 'Resuelto').length
  const pendientes = alertas.filter(a => a.estado === 'Pendiente').length
  const porTipo    = alertas.reduce((acc, a) => { acc[a.tipo] = (acc[a.tipo] ?? 0) + 1; return acc }, {})

  return (
    <div className="space-y-5">
      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-green-600 text-white text-sm font-medium px-4 py-2.5 rounded-xl shadow-lg">
          {toast}
        </div>
      )}

      {/* KPIs de alertas */}
      <div className="grid grid-cols-3 gap-3">
        <KpiCard
          label="Tasa de Resolución" value={`${Math.round(resueltas / alertas.length * 100)}%`}
          sub={`${resueltas} de ${alertas.length} alertas resueltas`}
          icon={CheckCircle}
          bg="bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-900"
          textMain="text-green-700 dark:text-green-300"
          textSub="text-green-600/70 dark:text-green-400/70"
          iconBg="bg-green-100 dark:bg-green-900"
        />
        <KpiCard
          label="Alertas Pendientes" value={String(pendientes).padStart(2, '0')}
          sub="Requieren acción inmediata"
          icon={AlertTriangle}
          bg="bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-900"
          textMain="text-red-600 dark:text-red-300"
          textSub="text-red-500/70 dark:text-red-400/70"
          iconBg="bg-red-100 dark:bg-red-900"
        />
        <div className="card p-4">
          <p className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wide mb-3">Desglose por tipo</p>
          <div className="space-y-1.5">
            {Object.entries(porTipo).map(([tipo, n]) => (
              <HBar key={tipo} label={tipo} value={n} max={alertas.length} colorClass="bg-orange-400" />
            ))}
          </div>
        </div>
      </div>

      {/* Filtros del grid */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide">Filtros:</span>
        {['', 'Alta', 'Media', 'Baja'].map(p => (
          <button key={p} onClick={() => { setFiltroPrio(p); setPagina(0) }}
            className={clsx('text-xs px-3 py-1 rounded-full border font-medium transition-colors',
              filtroPrio === p
                ? 'bg-brand-600 text-white border-brand-600'
                : 'bg-white dark:bg-slate-700 border-gray-200 dark:border-slate-600 text-gray-600 dark:text-slate-300'
            )}
          >{p || 'Prioridad: Todas'}</button>
        ))}
        <span className="text-gray-200 dark:text-slate-700">|</span>
        {['', 'Pendiente', 'En gestión', 'En taller', 'Resuelto'].map(e => (
          <button key={e} onClick={() => { setFiltroEst(e); setPagina(0) }}
            className={clsx('text-xs px-3 py-1 rounded-full border font-medium transition-colors',
              filtroEst === e
                ? 'bg-brand-600 text-white border-brand-600'
                : 'bg-white dark:bg-slate-700 border-gray-200 dark:border-slate-600 text-gray-600 dark:text-slate-300'
            )}
          >{e || 'Estado: Todos'}</button>
        ))}
        <span className="ml-auto text-xs text-gray-400 dark:text-slate-500">{filtradas.length} alertas</span>
      </div>

      {/* Data Grid */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 dark:bg-slate-900 border-b border-gray-200 dark:border-slate-700">
                {['ID', 'Fecha/Hora', 'Prioridad', 'Tipo de Incidencia', 'Vehículo', 'Cliente', 'Ruta', 'Descripción', 'Estado', 'Acción'].map(h => (
                  <th key={h} className="py-2.5 px-3 text-left font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {vista.length === 0 && (
                <tr><td colSpan={10} className="text-center py-10 text-gray-400 dark:text-slate-500">Sin alertas con ese filtro</td></tr>
              )}
              {vista.map(a => (
                <tr key={a.id} className="border-b border-gray-100 dark:border-slate-700/50 hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                  <td className="py-3 px-3 font-mono font-semibold text-gray-700 dark:text-slate-300 whitespace-nowrap">{a.id}</td>
                  <td className="py-3 px-3 tabular-nums text-gray-500 dark:text-slate-400 whitespace-nowrap">{a.fechaHora}</td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold text-xs', PRIORIDAD_CFG[a.prioridad]?.bg)}>
                      <span className={clsx('w-1.5 h-1.5 rounded-full', PRIORIDAD_CFG[a.prioridad]?.dot)} />
                      {a.prioridad}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-gray-700 dark:text-slate-300 whitespace-nowrap">{a.tipo}</td>
                  <td className="py-3 px-3 font-mono text-gray-700 dark:text-slate-300 whitespace-nowrap">{a.vehiculo}</td>
                  <td className="py-3 px-3 max-w-[140px]">
                    <span className="truncate block text-gray-600 dark:text-slate-400" title={a.cliente}>{a.cliente}</span>
                  </td>
                  <td className="py-3 px-3 text-gray-600 dark:text-slate-400 whitespace-nowrap">{a.ruta}</td>
                  <td className="py-3 px-3 max-w-[220px]">
                    <span className="text-gray-600 dark:text-slate-400 leading-relaxed">{a.desc}</span>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className={clsx('px-2 py-0.5 rounded-full text-xs font-semibold', ESTADO_CFG[a.estado] ?? '')}>{a.estado}</span>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    {a.estado !== 'Resuelto' ? (
                      <div className="flex gap-1">
                        {['Pendiente', 'En gestión'].includes(a.estado) && (
                          <button
                            onClick={() => asignarTaller(a.id)}
                            className="flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 hover:bg-blue-100 font-medium transition-colors"
                          >
                            <Wrench size={10} /> Taller
                          </button>
                        )}
                        <button
                          onClick={() => notificarOp(a.id)}
                          className="flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-orange-50 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300 hover:bg-orange-100 font-medium transition-colors"
                        >
                          <Bell size={10} /> Notificar
                        </button>
                      </div>
                    ) : (
                      <span className="text-gray-300 dark:text-slate-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-900">
          <span className="text-xs text-gray-400 dark:text-slate-500">
            Página {pagina + 1} de {paginas || 1} · {filtradas.length} registros
          </span>
          <div className="flex gap-1.5">
            <button
              disabled={pagina === 0}
              onClick={() => setPagina(p => p - 1)}
              className="btn-secondary px-2.5 py-1.5 disabled:opacity-40"
            ><ChevronLeft size={13} /></button>
            <button
              disabled={pagina >= paginas - 1}
              onClick={() => setPagina(p => p + 1)}
              className="btn-secondary px-2.5 py-1.5 disabled:opacity-40"
            ><ChevronRight size={13} /></button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Componente principal
// ─────────────────────────────────────────────────────────────────────────────

const TABS = [
  { id: 'general',  label: 'General'  },
  { id: 'clientes', label: 'Clientes' },
  { id: 'sedes',    label: 'Sedes'    },
  { id: 'alertas',  label: 'Alertas'  },
]

export default function Dashboard() {
  const { user } = useAuth()
  const [tab, setTab]   = useState('general')
  const [fecha, setFecha] = useState(format(new Date(), 'yyyy-MM-dd'))

  const { data: servicios = [], isLoading, refetch } = useQuery({
    queryKey:       ['servicios', user?.sede_id, fecha],
    queryFn:        () => getServicios(user.sede_id, fecha),
    enabled:        !!user?.sede_id,
    refetchInterval: 60_000,
  })

  function cambiarFecha(dias) {
    if (dias === 0) { setFecha(format(new Date(), 'yyyy-MM-dd')); return }
    const d = new Date(fecha + 'T12:00:00')
    d.setDate(d.getDate() + dias)
    setFecha(format(d, 'yyyy-MM-dd'))
  }

  return (
    <div className="p-6 space-y-5">
      {/* Barra de tabs */}
      <div className="flex gap-1 p-1 bg-gray-100 dark:bg-slate-800 rounded-xl w-fit">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={clsx(
              'px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-150',
              tab === t.id
                ? 'bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 shadow-sm'
                : 'text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Contenido por tab */}
      {tab === 'general'  && (
        <TabGeneral
          servicios={servicios}
          fecha={fecha}
          cambiarFecha={cambiarFecha}
          isLoading={isLoading}
          refetch={refetch}
        />
      )}
      {tab === 'clientes' && <TabClientes servicios={servicios} />}
      {tab === 'sedes'    && <TabSedes />}
      {tab === 'alertas'  && <TabAlertas />}
    </div>
  )
}
