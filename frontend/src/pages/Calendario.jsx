import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, startOfWeek, addDays, addWeeks, subWeeks, isSameDay, isToday } from 'date-fns'
import { es } from 'date-fns/locale'
import { useAuth } from '../context/AuthContext'
import { getServicios } from '../api/servicios'
import { EstadoBadge } from '../components/ui/Badge'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

// Carga los 7 días de la semana en paralelo
function useSemanaServicios(sedeId, inicioSemana) {
  const dias = Array.from({ length: 7 }, (_, i) => addDays(inicioSemana, i))
  const fechas = dias.map(d => format(d, 'yyyy-MM-dd'))

  // Una sola query por semana — necesitaríamos múltiples queries o un endpoint de rango
  // Por ahora hacemos 7 queries en paralelo con React Query
  const queries = fechas.map((f) => ({
    queryKey: ['servicios', sedeId, f],
    queryFn:  () => getServicios(sedeId, f),
    enabled:  !!sedeId,
    staleTime: 60_000,
  }))

  // useQueries no está disponible sin importarlo explícitamente
  return { dias, fechas }
}

function DayColumn({ sedeId, fecha, dia }) {
  const { data: servicios = [], isLoading } = useQuery({
    queryKey: ['servicios', sedeId, format(fecha, 'yyyy-MM-dd')],
    queryFn:  () => getServicios(sedeId, format(fecha, 'yyyy-MM-dd')),
    enabled:  !!sedeId,
    staleTime: 60_000,
  })

  const hoy = isToday(fecha)
  const prog      = servicios.filter(s => s.estado === 'PROGRAMADO').length
  const en_curso  = servicios.filter(s => s.estado === 'EN_CURSO').length
  const completado= servicios.filter(s => s.estado === 'COMPLETADO').length
  const cancelado = servicios.filter(s => s.estado === 'CANCELADO').length

  return (
    <div className={clsx(
      'flex flex-col border-r border-gray-200 dark:border-slate-700 last:border-r-0',
      hoy ? 'bg-brand-50 dark:bg-blue-900/20' : 'dark:bg-slate-800'
    )}>
      {/* Header del día */}
      <div className={clsx(
        'px-2 py-3 text-center border-b border-gray-200 dark:border-slate-700',
        hoy && 'bg-brand-600 text-white'
      )}>
        <p className={clsx('text-xs font-semibold uppercase tracking-wider', hoy ? 'text-brand-100' : 'text-gray-500 dark:text-slate-400')}>
          {format(fecha, 'EEE', { locale: es })}
        </p>
        <p className={clsx('text-xl font-bold mt-0.5', hoy ? 'text-white' : 'text-gray-900 dark:text-slate-100')}>
          {format(fecha, 'd')}
        </p>
        <p className={clsx('text-xs mt-0.5', hoy ? 'text-brand-100' : 'text-gray-400 dark:text-slate-500')}>
          {servicios.length} serv.
        </p>
      </div>

      {/* Pastillas de resumen */}
      {servicios.length > 0 && (
        <div className="flex flex-wrap gap-1 p-2 border-b border-gray-100 dark:border-slate-700/50">
          {prog      > 0 && <span className="badge bg-yellow-100 text-yellow-800">{prog}  prog.</span>}
          {en_curso  > 0 && <span className="badge bg-green-100  text-green-800">{en_curso} curso</span>}
          {completado> 0 && <span className="badge bg-blue-100   text-blue-800">{completado} ok</span>}
          {cancelado > 0 && <span className="badge bg-red-100    text-red-700">{cancelado} canc.</span>}
        </div>
      )}

      {/* Lista de servicios */}
      <div className="flex-1 overflow-y-auto p-1.5 space-y-1">
        {isLoading && (
          <p className="text-xs text-gray-400 dark:text-slate-500 text-center py-4">Cargando...</p>
        )}
        {!isLoading && servicios.length === 0 && (
          <p className="text-xs text-gray-300 dark:text-slate-600 text-center py-4">—</p>
        )}
        {servicios.map((s) => {
          const hora = s.hora_inicio?.slice(0, 5) ?? '--:--'
          const ruta = s.ruta_nombre ?? `Ruta ${s.ruta_id}`
          const colorBg = {
            PROGRAMADO: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-700/50',
            EN_CURSO:   'bg-green-50  dark:bg-green-900/20  border-green-200  dark:border-green-700/50',
            COMPLETADO: 'bg-blue-50   dark:bg-blue-900/20   border-blue-200   dark:border-blue-700/50',
            CANCELADO:  'bg-gray-50   dark:bg-slate-700/30  border-gray-200   dark:border-slate-600/50 opacity-50',
          }[s.estado] ?? 'bg-white dark:bg-slate-700 border-gray-200 dark:border-slate-600'

          return (
            <div key={s.servicio_id} className={clsx('rounded-md border p-1.5 text-xs', colorBg)}>
              <p className="font-semibold text-gray-900 dark:text-slate-100">{hora}</p>
              <p className="text-gray-600 dark:text-slate-300 truncate mt-0.5" title={ruta}>{ruta}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function Calendario() {
  const { user } = useAuth()
  const [semana, setSemana] = useState(() => startOfWeek(new Date(), { weekStartsOn: 1 }))

  const diasSemana = Array.from({ length: 7 }, (_, i) => addDays(semana, i))
  const semanaLabel = `${format(semana, "d 'de' MMM", { locale: es })} — ${format(diasSemana[6], "d 'de' MMM yyyy", { locale: es })}`

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Calendario semanal</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400 capitalize mt-0.5">{semanaLabel}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setSemana(s => subWeeks(s, 1))} className="btn-secondary px-2">
            <ChevronLeft size={16} />
          </button>
          <button
            onClick={() => setSemana(startOfWeek(new Date(), { weekStartsOn: 1 }))}
            className="btn-secondary text-xs px-3"
          >
            Esta semana
          </button>
          <button onClick={() => setSemana(s => addWeeks(s, 1))} className="btn-secondary px-2">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* Grid de 7 días */}
      <div className="flex-1 card p-0 overflow-hidden grid grid-cols-7 min-h-0">
        {diasSemana.map((dia) => (
          <DayColumn
            key={dia.toISOString()}
            sedeId={user?.sede_id}
            fecha={dia}
            dia={dia}
          />
        ))}
      </div>
    </div>
  )
}
