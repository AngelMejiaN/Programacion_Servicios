import { useState, useMemo } from 'react'
import { useQueries } from '@tanstack/react-query'
import { format, startOfWeek, addDays, addWeeks, subWeeks, isToday } from 'date-fns'
import { es } from 'date-fns/locale'
import { useAuth } from '../context/AuthContext'
import { getServicios } from '../api/servicios'
import { EstadoBadge } from '../components/ui/Badge'
import { ChevronLeft, ChevronRight, X, Search } from 'lucide-react'
import clsx from 'clsx'

// ─────────────────────────────────────────────────────────────────────────────
// Bloques horarios fijos de la operación
// ─────────────────────────────────────────────────────────────────────────────

const BLOQUES = [
  {
    id: 'madrugada', label: 'Madrugada', rango: '05:00–08:00',
    horaInicio: 5,  horaFin: 8,
    accent:     'bg-indigo-500',
    textAccent: 'text-indigo-700 dark:text-indigo-300',
    hoverRing:  'hover:ring-indigo-200 dark:hover:ring-indigo-800',
    hoverBorder:'hover:border-indigo-300 dark:hover:border-indigo-700',
  },
  {
    id: 'manana', label: 'Mañana', rango: '08:00–12:00',
    horaInicio: 8,  horaFin: 12,
    accent:     'bg-amber-400',
    textAccent: 'text-amber-700 dark:text-amber-300',
    hoverRing:  'hover:ring-amber-200 dark:hover:ring-amber-800',
    hoverBorder:'hover:border-amber-300 dark:hover:border-amber-700',
  },
  {
    id: 'tarde', label: 'Tarde', rango: '12:00–17:00',
    horaInicio: 12, horaFin: 17,
    accent:     'bg-orange-500',
    textAccent: 'text-orange-700 dark:text-orange-300',
    hoverRing:  'hover:ring-orange-200 dark:hover:ring-orange-800',
    hoverBorder:'hover:border-orange-300 dark:hover:border-orange-700',
  },
  {
    id: 'noche', label: 'Noche', rango: '17:00–22:00',
    horaInicio: 17, horaFin: 22,
    accent:     'bg-violet-500',
    textAccent: 'text-violet-700 dark:text-violet-300',
    hoverRing:  'hover:ring-violet-200 dark:hover:ring-violet-800',
    hoverBorder:'hover:border-violet-300 dark:hover:border-violet-700',
  },
  {
    id: 'trasnoche', label: 'Trasnoche', rango: '22:00–05:00',
    horaInicio: 22, horaFin: 5,
    accent:     'bg-slate-500',
    textAccent: 'text-slate-600 dark:text-slate-400',
    hoverRing:  'hover:ring-slate-200 dark:hover:ring-slate-600',
    hoverBorder:'hover:border-slate-300 dark:hover:border-slate-600',
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function inBloque(s, bloque) {
  const h = parseInt(s.hora_inicio?.slice(0, 2) ?? '0')
  if (bloque.horaInicio < bloque.horaFin) {
    return h >= bloque.horaInicio && h < bloque.horaFin
  }
  return h >= bloque.horaInicio || h < bloque.horaFin
}

function computeStats(svs) {
  const total      = svs.length
  const completado = svs.filter(s => s.estado === 'COMPLETADO').length
  const cancelado  = svs.filter(s => s.estado === 'CANCELADO').length
  const en_curso   = svs.filter(s => s.estado === 'EN_CURSO').length
  const prog       = svs.filter(s => s.estado === 'PROGRAMADO').length

  const conDatos = svs.filter(
    s => s.estado === 'COMPLETADO' && s.hora_llegada_real && s.hora_llegada_est
  )
  const aTiempo = conDatos.filter(
    s => s.hora_llegada_real.slice(0, 5) <= s.hora_llegada_est.slice(0, 5)
  ).length
  const sla = conDatos.length > 0 ? Math.round(aTiempo / conDatos.length * 100) : null

  return { total, completado, cancelado, en_curso, prog, sla }
}

// ─────────────────────────────────────────────────────────────────────────────
// GridCell — tarjeta resumen de cada celda (día × bloque)
// ─────────────────────────────────────────────────────────────────────────────

function GridCell({ svs, isLoading, bloque, onClick }) {
  const s = useMemo(() => computeStats(svs), [svs])

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 animate-pulse min-h-[96px]" />
    )
  }

  if (s.total === 0) {
    return (
      <div className="rounded-xl border border-dashed border-gray-200 dark:border-slate-700/60 flex items-center justify-center min-h-[96px]">
        <span className="text-xs text-gray-300 dark:text-slate-600">—</span>
      </div>
    )
  }

  const slaBar  = s.sla === null ? null : s.sla >= 90 ? 'bg-green-500' : s.sla >= 75 ? 'bg-amber-400' : 'bg-red-400'
  const slaText = s.sla === null ? null : s.sla >= 90 ? 'text-green-600 dark:text-green-400' : s.sla >= 75 ? 'text-amber-600 dark:text-amber-400' : 'text-red-500 dark:text-red-400'

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full min-h-[96px] rounded-xl border bg-white dark:bg-slate-800 text-left p-2.5',
        'border-gray-200 dark:border-slate-700',
        bloque.hoverBorder,
        'hover:shadow-md hover:ring-2',
        bloque.hoverRing,
        'transition-all duration-150',
      )}
    >
      {/* Total */}
      <div className="flex items-baseline gap-1 mb-1.5">
        <span className="text-xl font-bold tabular-nums text-gray-900 dark:text-slate-100">{s.total}</span>
        <span className="text-xs text-gray-400 dark:text-slate-500">serv.</span>
      </div>

      {/* Barra de SLA */}
      {slaBar !== null && (
        <div className="mb-2">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-gray-400 dark:text-slate-500 leading-none" style={{ fontSize: 10 }}>SLA</span>
            <span className={clsx('font-bold leading-none tabular-nums', slaText)} style={{ fontSize: 10 }}>
              {s.sla}%
            </span>
          </div>
          <div className="h-1.5 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={clsx('h-full rounded-full transition-all duration-500', slaBar)}
              style={{ width: `${s.sla}%` }}
            />
          </div>
        </div>
      )}

      {/* Mini contadores de estado */}
      <div className="flex flex-wrap gap-x-2 gap-y-0.5">
        {s.completado > 0 && (
          <span className="text-green-600 dark:text-green-400 font-semibold tabular-nums" style={{ fontSize: 11 }}>
            🟢 {s.completado}
          </span>
        )}
        {s.en_curso > 0 && (
          <span className="text-amber-500 dark:text-amber-400 font-semibold tabular-nums" style={{ fontSize: 11 }}>
            🟡 {s.en_curso}
          </span>
        )}
        {s.prog > 0 && (
          <span className="text-blue-500 dark:text-blue-400 font-semibold tabular-nums" style={{ fontSize: 11 }}>
            ⚪ {s.prog}
          </span>
        )}
        {s.cancelado > 0 && (
          <span className="text-red-500 dark:text-red-400 font-semibold tabular-nums" style={{ fontSize: 11 }}>
            🔴 {s.cancelado}
          </span>
        )}
      </div>
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ServiceDrawer — panel deslizable lateral (Capa 1)
// ─────────────────────────────────────────────────────────────────────────────

function ServiceDrawer({ open, titulo, subtitulo, servicios, busqueda, setBusqueda, onClose, onSelect }) {
  const filtrados = useMemo(() => {
    const q = busqueda.toLowerCase().trim()
    if (!q) return servicios
    return servicios.filter(s =>
      s.cliente_nombre?.toLowerCase().includes(q) ||
      s.vehiculo_placa?.toLowerCase().includes(q)
    )
  }, [servicios, busqueda])

  return (
    <>
      {/* Backdrop */}
      <div
        className={clsx(
          'fixed inset-0 bg-black/40 z-40 transition-opacity duration-300',
          open ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
      />

      {/* Panel lateral */}
      <div
        className={clsx(
          'fixed top-0 right-0 h-full w-[420px] max-w-[92vw]',
          'bg-white dark:bg-slate-800 shadow-2xl z-50 flex flex-col',
          'transition-transform duration-300 ease-in-out',
          open ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Cabecera */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-gray-100 dark:border-slate-700 shrink-0">
          <div className="min-w-0 pr-3">
            <p className="font-bold text-gray-900 dark:text-slate-100 leading-tight">{titulo}</p>
            <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{subtitulo}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors shrink-0"
          >
            <X size={18} />
          </button>
        </div>

        {/* Buscador */}
        <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-700 shrink-0">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              className="input pl-9 text-sm w-full"
              placeholder="Filtrar por cliente o vehículo..."
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
            />
          </div>
          {busqueda.trim() && (
            <p className="text-xs text-gray-400 dark:text-slate-500 mt-1.5 px-1">
              {filtrados.length} de {servicios.length} servicios
            </p>
          )}
        </div>

        {/* Lista scrollable */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {filtrados.length === 0 && (
            <div className="flex flex-col items-center justify-center py-14 gap-2 text-center">
              <Search size={28} className="text-gray-200 dark:text-slate-700" />
              <p className="text-sm text-gray-400 dark:text-slate-500">
                {busqueda ? `Sin resultados para "${busqueda}"` : 'Sin servicios en este bloque'}
              </p>
            </div>
          )}

          {filtrados.map(s => (
            <button
              key={s.servicio_id}
              onClick={() => onSelect(s)}
              className={clsx(
                'w-full text-left rounded-xl border p-3 transition-all duration-150',
                'border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800/50',
                'hover:border-brand-400 dark:hover:border-brand-600',
                'hover:bg-brand-50 dark:hover:bg-brand-900/20',
                'hover:shadow-sm',
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-mono text-gray-400 dark:text-slate-500 mb-0.5">
                    #{s.servicio_id} · {s.hora_inicio?.slice(0, 5) ?? '--:--'}
                  </p>
                  <p className="text-sm font-semibold text-gray-800 dark:text-slate-100 truncate">
                    {s.cliente_nombre ?? '—'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-slate-400 truncate mt-0.5">
                    {s.ruta_nombre ?? '—'}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <span className="text-xs font-mono font-bold text-gray-600 dark:text-slate-300">
                    {s.vehiculo_placa ?? `#${s.vehiculo_id}`}
                  </span>
                  <EstadoBadge estado={s.estado} />
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ServiceModal — popup de ficha técnica del servicio (Capa 2)
// ─────────────────────────────────────────────────────────────────────────────

function Field({ label, value, mono = false, accent }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wide mb-0.5">
        {label}
      </p>
      <p className={clsx('text-sm', mono && 'font-mono', accent ?? 'text-gray-800 dark:text-slate-200')}>
        {value || '—'}
      </p>
    </div>
  )
}

function ServiceModal({ servicio, onClose }) {
  if (!servicio) return null

  const esCompletado = servicio.estado === 'COMPLETADO'

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Cabecera del modal */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-50 dark:bg-slate-900 border-b border-gray-100 dark:border-slate-700">
          <div>
            <p className="font-bold text-gray-900 dark:text-slate-100">Ficha del servicio</p>
            <p className="text-xs font-mono text-gray-400 dark:text-slate-500 mt-0.5">
              #{servicio.servicio_id}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <EstadoBadge estado={servicio.estado} />
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Cuerpo */}
        <div className="px-6 py-5 space-y-4">
          <Field label="Cliente" value={servicio.cliente_nombre} />
          <Field label="Ruta"    value={servicio.ruta_nombre} />

          <div className="grid grid-cols-2 gap-4">
            <Field
              label="Vehículo"
              value={servicio.vehiculo_placa ?? `#${servicio.vehiculo_id}`}
              mono
            />
            <Field
              label="Horario de salida"
              value={servicio.hora_inicio?.slice(0, 5)}
              mono
            />
          </div>

          {/* Llegada condicional — lógica obligatoria */}
          <div className="pt-1 border-t border-gray-100 dark:border-slate-700">
            {esCompletado ? (
              <div className="flex items-center gap-3 bg-green-50 dark:bg-green-900/20 rounded-xl px-4 py-3.5">
                <span className="text-2xl" role="img" aria-label="completado">✅</span>
                <div>
                  <p className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase tracking-wide">
                    Hora de Llegada Real
                  </p>
                  <p className="text-xl font-bold font-mono text-green-700 dark:text-green-300 mt-0.5">
                    {servicio.hora_llegada_real?.slice(0, 5) ?? 'No registrada'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl px-4 py-3.5">
                <span className="text-2xl" role="img" aria-label="estimado">🕐</span>
                <div>
                  <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wide">
                    Hora de Llegada Estimada
                  </p>
                  <p className="text-xl font-bold font-mono text-blue-700 dark:text-blue-300 mt-0.5">
                    {servicio.hora_llegada_est?.slice(0, 5) ?? 'No disponible'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 pb-5">
          <button onClick={onClose} className="btn-secondary">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Calendario — componente principal
// ─────────────────────────────────────────────────────────────────────────────

export default function Calendario() {
  const { user } = useAuth()

  const [semana, setSemana] = useState(() => startOfWeek(new Date(), { weekStartsOn: 1 }))

  // Estado del drawer: guarda índice del día y id del bloque (no los datos)
  // Los datos se derivan reactivamente desde queries para mantenerse sincronizados
  const [drawer, setDrawer] = useState({ open: false, diaIdx: null, bloqueId: null })
  const [busqueda, setBusqueda]   = useState('')
  const [modalSv, setModalSv]     = useState(null)

  const dias   = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(semana, i)), [semana])
  const fechas = useMemo(() => dias.map(d => format(d, 'yyyy-MM-dd')), [dias])

  // 7 queries en paralelo — reutiliza caché de React Query (mismas queryKeys que Dashboard)
  const queries = useQueries({
    queries: fechas.map(f => ({
      queryKey:  ['servicios', user?.sede_id, f],
      queryFn:   () => getServicios(user.sede_id, f),
      enabled:   !!user?.sede_id,
      staleTime: 60_000,
    })),
  })

  // Bloque activo derivado del estado del drawer
  const bloqueActivo = useMemo(
    () => BLOQUES.find(b => b.id === drawer.bloqueId) ?? null,
    [drawer.bloqueId]
  )

  // Servicios del drawer derivados reactivamente desde las queries
  const drawerSvs = useMemo(() => {
    if (!drawer.open || drawer.diaIdx === null || !bloqueActivo) return []
    const svsDelDia = queries[drawer.diaIdx]?.data ?? []
    return svsDelDia.filter(s => inBloque(s, bloqueActivo))
  }, [drawer, queries, bloqueActivo])

  // Título del drawer
  const drawerTitulo = useMemo(() => {
    if (drawer.diaIdx === null) return ''
    const s = format(dias[drawer.diaIdx], "EEEE d 'de' MMMM", { locale: es })
    return s.charAt(0).toUpperCase() + s.slice(1)
  }, [drawer.diaIdx, dias])

  const semanaLabel = `${format(semana, "d 'de' MMM", { locale: es })} — ${format(dias[6], "d 'de' MMM yyyy", { locale: es })}`

  function navSemana(fn) {
    setSemana(fn)
    setDrawer(d => ({ ...d, open: false }))  // cerrar drawer al cambiar semana
  }

  function abrirDrawer(diaIdx, bloqueId) {
    setBusqueda('')
    setDrawer({ open: true, diaIdx, bloqueId })
  }

  function cerrarDrawer() { setDrawer(d => ({ ...d, open: false })) }
  function cerrarModal()  { setModalSv(null) }

  return (
    <div className="p-6 flex flex-col gap-4 h-full min-h-0">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between shrink-0 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Calendario semanal</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5 capitalize">{semanaLabel}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => navSemana(s => subWeeks(s, 1))} className="btn-secondary px-2.5 py-1.5">
            <ChevronLeft size={16} />
          </button>
          <button
            onClick={() => navSemana(() => startOfWeek(new Date(), { weekStartsOn: 1 }))}
            className="btn-secondary text-xs px-3 py-1.5"
          >
            Esta semana
          </button>
          <button onClick={() => navSemana(s => addWeeks(s, 1))} className="btn-secondary px-2.5 py-1.5">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* ── Leyenda de bloques ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-4 flex-wrap shrink-0">
        {BLOQUES.map(b => (
          <span key={b.id} className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-slate-400">
            <span className={clsx('w-2 h-2 rounded-full shrink-0', b.accent)} />
            <span className="font-semibold">{b.label}</span>
            <span className="text-gray-300 dark:text-slate-600">{b.rango}</span>
          </span>
        ))}
        <span className="ml-auto text-xs text-gray-300 dark:text-slate-600 hidden sm:block">
          Haz clic en una celda para ver los servicios
        </span>
      </div>

      {/* ── Matriz horaria ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto min-h-0">
        <div className="flex flex-col gap-1.5 min-w-[780px] pb-2">

          {/* Fila de cabeceras — nombres de días */}
          <div
            className="grid gap-1.5"
            style={{ gridTemplateColumns: '88px repeat(7, 1fr)' }}
          >
            <div /> {/* celda vacía top-left */}
            {dias.map((dia, i) => {
              const hoy = isToday(dia)
              return (
                <div
                  key={i}
                  className={clsx(
                    'rounded-xl py-2.5 text-center',
                    hoy ? 'bg-brand-600' : 'bg-gray-100 dark:bg-slate-800'
                  )}
                >
                  <p className={clsx(
                    'text-xs font-semibold uppercase tracking-wider',
                    hoy ? 'text-brand-100' : 'text-gray-500 dark:text-slate-400'
                  )}>
                    {format(dia, 'EEE', { locale: es })}
                  </p>
                  <p className={clsx(
                    'text-lg font-bold mt-0.5',
                    hoy ? 'text-white' : 'text-gray-900 dark:text-slate-100'
                  )}>
                    {format(dia, 'd')}
                  </p>
                </div>
              )
            })}
          </div>

          {/* Filas de bloques */}
          {BLOQUES.map(bloque => (
            <div
              key={bloque.id}
              className="grid gap-1.5"
              style={{ gridTemplateColumns: '88px repeat(7, 1fr)' }}
            >
              {/* Etiqueta lateral del bloque */}
              <div className="flex flex-col items-center justify-center gap-1 rounded-xl bg-gray-50 dark:bg-slate-800/50 py-3 px-1 min-h-[96px]">
                <div className={clsx('w-1.5 h-8 rounded-full shrink-0', bloque.accent)} />
                <span className={clsx('text-xs font-bold text-center leading-tight mt-1', bloque.textAccent)}>
                  {bloque.label}
                </span>
                <span
                  className="text-center leading-tight text-gray-400 dark:text-slate-500 mt-0.5"
                  style={{ fontSize: 9 }}
                >
                  {bloque.rango}
                </span>
              </div>

              {/* Celdas: una por cada día de la semana */}
              {dias.map((_, diaIdx) => {
                const svsDelDia = queries[diaIdx].data ?? []
                const svsCelda  = svsDelDia.filter(s => inBloque(s, bloque))
                return (
                  <GridCell
                    key={diaIdx}
                    svs={svsCelda}
                    isLoading={queries[diaIdx].isLoading}
                    bloque={bloque}
                    onClick={() => svsCelda.length > 0 && abrirDrawer(diaIdx, bloque.id)}
                  />
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* ── Capa 1: Sliding Drawer ─────────────────────────────────────────── */}
      <ServiceDrawer
        open={drawer.open}
        titulo={drawerTitulo}
        subtitulo={
          bloqueActivo
            ? `${bloqueActivo.label} (${bloqueActivo.rango}) · ${drawerSvs.length} servicios`
            : ''
        }
        servicios={drawerSvs}
        busqueda={busqueda}
        setBusqueda={setBusqueda}
        onClose={cerrarDrawer}
        onSelect={sv => setModalSv(sv)}
      />

      {/* ── Capa 2: Modal de detalle ───────────────────────────────────────── */}
      <ServiceModal servicio={modalSv} onClose={cerrarModal} />
    </div>
  )
}
