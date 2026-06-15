import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import { useAuth } from '../context/AuthContext'
import { getServicios, cambiarEstado } from '../api/servicios'
import { EstadoBadge } from '../components/ui/Badge'
import { RefreshCw, ChevronLeft, ChevronRight, Bus, ArrowRight, ArrowLeft } from 'lucide-react'
import clsx from 'clsx'

const ESTADOS = ['', 'PROGRAMADO', 'EN_CURSO', 'COMPLETADO', 'CANCELADO']

// ── Expande cada servicio en filas de Ida y (si aplica) Retorno ──────────────
function expandirServicios(servicios) {
  const filas = []

  for (const s of servicios) {
    // Hora para ordenar
    const horaIdaStr     = s.hora_inicio?.slice(0, 5) ?? '00:00'
    const horaRetornoStr = s.hora_salida_planta?.slice(0, 5) ?? null

    // ── Fila IDA ──────────────────────────────────────────────────────────────
    filas.push({
      key:       `${s.servicio_id}-ida`,
      servicio:  s,
      tipo:      'ida',
      horaSort:  horaIdaStr,
      hora:      horaIdaStr,
      horaEst:   s.hora_llegada_est?.slice(0, 5) ?? null,
      horaReal:  s.hora_llegada_real?.slice(0, 5) ?? null,
      placa:     s.vehiculo_placa  ?? `#${s.vehiculo_id}`,
      ruta:      s.ruta_nombre     ?? `Ruta #${s.ruta_id}`,
      cliente:   s.cliente_nombre  ?? '',
      paradero:  s.paradero_origen_nombre ?? null,
      estado:    s.estado,
    })

    // ── Fila RETORNO — solo si tiene hora_salida_planta ───────────────────────
    if (horaRetornoStr) {
      const placaRet = s.retorno_vehiculo_id
        ? `#${s.retorno_vehiculo_id}`
        : s.vehiculo_placa ?? `#${s.vehiculo_id}`

      filas.push({
        key:      `${s.servicio_id}-ret`,
        servicio: s,
        tipo:     'retorno',
        horaSort: horaRetornoStr,
        hora:     horaRetornoStr,
        horaEst:  s.hora_retorno_est?.slice(0, 5) ?? null,
        horaReal: s.hora_retorno_real?.slice(0, 5) ?? null,
        placa:    placaRet,
        ruta:     s.ruta_nombre    ?? `Ruta #${s.ruta_id}`,
        cliente:  s.cliente_nombre ?? '',
        paradero: null,
        estado:   s.hora_retorno_real ? 'COMPLETADO'
                : s.hora_salida_planta ? s.estado
                : 'PROGRAMADO',
      })
    }
  }

  // Ordenar todo por hora
  filas.sort((a, b) => a.horaSort.localeCompare(b.horaSort))
  return filas
}

export default function Dashboard() {
  const { user }  = useAuth()
  const qc        = useQueryClient()
  const [fecha, setFecha]               = useState(format(new Date(), 'yyyy-MM-dd'))
  const [filtroEstado, setFiltroEstado] = useState('')

  const { data: servicios = [], isLoading, refetch } = useQuery({
    queryKey: ['servicios', user?.sede_id, fecha, filtroEstado],
    queryFn:  () => getServicios(user.sede_id, fecha, filtroEstado || undefined),
    enabled:  !!user?.sede_id,
    refetchInterval: 60_000,
  })

  const mutacion = useMutation({
    mutationFn: ({ id, estado }) => cambiarEstado(id, estado),
    onSuccess:  () => qc.invalidateQueries(['servicios']),
  })

  const cambiarFecha = (dias) => {
    const d = new Date(fecha + 'T12:00:00')
    d.setDate(d.getDate() + dias)
    setFecha(format(d, 'yyyy-MM-dd'))
  }

  const stats = {
    programado: servicios.filter(s => s.estado === 'PROGRAMADO').length,
    en_curso:   servicios.filter(s => s.estado === 'EN_CURSO').length,
    completado: servicios.filter(s => s.estado === 'COMPLETADO').length,
    cancelado:  servicios.filter(s => s.estado === 'CANCELADO').length,
  }

  const fechaDisplay = format(new Date(fecha + 'T12:00:00'), "EEEE d 'de' MMMM", { locale: es })
  const esHoy = fecha === format(new Date(), 'yyyy-MM-dd')

  const filas = expandirServicios(servicios)
  const totalMovimientos = filas.length

  return (
    <div className="p-6 space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-sm text-gray-600 dark:text-slate-300 capitalize font-medium">{fechaDisplay}</p>
          <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">
            {servicios.length} servicios · {totalMovimientos} movimientos · Sede {user?.sede_id}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => cambiarFecha(-1)} className="btn-secondary px-2.5 py-1.5"><ChevronLeft size={15} /></button>
          <button
            onClick={() => setFecha(format(new Date(), 'yyyy-MM-dd'))}
            className={clsx('btn-secondary text-xs px-3 py-1.5',
              esHoy && 'bg-brand-50 dark:bg-brand-900/50 border-brand-300 dark:border-brand-700 text-brand-700 dark:text-brand-300 font-semibold'
            )}
          >Hoy</button>
          <button onClick={() => cambiarFecha(1)} className="btn-secondary px-2.5 py-1.5"><ChevronRight size={15} /></button>
          <button onClick={() => refetch()} className="btn-secondary px-2.5 py-1.5" title="Actualizar">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Programados', value: stats.programado, cls: 'border-yellow-400 dark:border-yellow-600 bg-yellow-50 dark:bg-yellow-950/60 text-yellow-700 dark:text-yellow-300' },
          { label: 'En curso',    value: stats.en_curso,   cls: 'border-green-400  dark:border-green-600  bg-green-50  dark:bg-green-950/60  text-green-700  dark:text-green-300'  },
          { label: 'Completados', value: stats.completado, cls: 'border-blue-400   dark:border-blue-600   bg-blue-50   dark:bg-blue-950/60   text-blue-700   dark:text-blue-300'   },
          { label: 'Cancelados',  value: stats.cancelado,  cls: 'border-red-400    dark:border-red-600    bg-red-50    dark:bg-red-950/60    text-red-600    dark:text-red-300'    },
        ].map(({ label, value, cls }) => (
          <div key={label} className={clsx('rounded-xl border-2 px-4 py-3.5 text-center', cls)}>
            <p className="text-3xl font-bold">{value}</p>
            <p className="text-xs font-semibold mt-1 opacity-75 uppercase tracking-wide">{label}</p>
          </div>
        ))}
      </div>

      {/* Tabla */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 shadow-sm overflow-hidden">

        {/* Filtros */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 flex-wrap">
          <span className="text-xs font-medium text-gray-400 dark:text-slate-500 mr-1">Estado:</span>
          {ESTADOS.map(e => (
            <button key={e} onClick={() => setFiltroEstado(e)}
              className={clsx('text-xs px-3 py-1 rounded-full font-medium transition-colors border',
                filtroEstado === e
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'bg-white dark:bg-slate-700 border-gray-200 dark:border-slate-600 text-gray-600 dark:text-slate-300 hover:border-brand-400'
              )}>
              {e || 'Todos'}
            </button>
          ))}
          {/* Leyenda */}
          <div className="ml-auto flex items-center gap-3 text-xs text-gray-400 dark:text-slate-500">
            <span className="flex items-center gap-1">
              <ArrowRight size={11} className="text-blue-500" /> Ida
            </span>
            <span className="flex items-center gap-1">
              <ArrowLeft size={11} className="text-teal-500" /> Retorno
            </span>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-gray-400 dark:text-slate-500">
            <RefreshCw size={20} className="animate-spin mr-2" /> Cargando...
          </div>
        ) : filas.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400 dark:text-slate-500">
            <Bus size={36} className="mb-3 opacity-25" />
            <p className="font-medium text-sm">Sin servicios para este día</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 dark:bg-slate-900 border-b border-gray-200 dark:border-slate-700 text-left">
                  {['Hora', 'Tipo', 'Cliente', 'Ruta', 'Vehículo', 'Llega est.', 'Llega real', 'Estado', 'Acciones'].map(h => (
                    <th key={h} className="py-2.5 px-3 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filas.map((fila, idx) => {
                  const esIda     = fila.tipo === 'ida'
                  const esRetorno = fila.tipo === 'retorno'
                  const s         = fila.servicio

                  // Separador visual cuando cambia el servicio padre
                  const prevFila = filas[idx - 1]
                  const esPrimerDelServicio = !prevFila || prevFila.servicio.servicio_id !== s.servicio_id

                  return (
                    <tr key={fila.key}
                      className={clsx(
                        'transition-colors',
                        esPrimerDelServicio && idx > 0 && 'border-t-2 border-gray-200 dark:border-slate-600',
                        esIda     && 'hover:bg-blue-50/30  dark:hover:bg-blue-950/10',
                        esRetorno && 'hover:bg-teal-50/30  dark:hover:bg-teal-950/10 bg-gray-50/50 dark:bg-slate-800/50',
                        !esIda && !esRetorno && 'hover:bg-gray-50 dark:hover:bg-slate-700/30',
                      )}>

                      {/* Hora */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <span className="text-sm font-bold tabular-nums text-gray-900 dark:text-slate-100">{fila.hora}</span>
                        {esPrimerDelServicio && (
                          <p className="text-xs text-gray-400 dark:text-slate-500">#{s.servicio_id}</p>
                        )}
                      </td>

                      {/* Tipo Ida / Retorno */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        {esIda ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                            <ArrowRight size={10} /> Ida
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300">
                            <ArrowLeft size={10} /> Retorno
                            {!s.retorno_misma_unidad && <span className="text-xs opacity-70 ml-0.5">· otra unidad</span>}
                          </span>
                        )}
                      </td>

                      {/* Cliente */}
                      <td className="py-3 px-3">
                        {esPrimerDelServicio && fila.cliente ? (
                          <span className="text-xs font-medium text-gray-500 dark:text-slate-400 bg-gray-100 dark:bg-slate-700 px-2 py-0.5 rounded-full">
                            {fila.cliente}
                          </span>
                        ) : <span className="text-gray-200 dark:text-slate-700 text-xs">↑</span>}
                      </td>

                      {/* Ruta */}
                      <td className="py-3 px-3 max-w-[180px]">
                        {esPrimerDelServicio ? (
                          <p className="text-sm font-medium text-gray-900 dark:text-slate-100 truncate" title={fila.ruta}>
                            {fila.ruta}
                          </p>
                        ) : (
                          <p className="text-xs text-gray-400 dark:text-slate-500 truncate pl-2">
                            ↩ {fila.ruta}
                          </p>
                        )}
                      </td>

                      {/* Vehículo */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <span className={clsx(
                          'text-sm font-mono font-semibold',
                          esIda     ? 'text-gray-700 dark:text-slate-300'
                                    : 'text-teal-700 dark:text-teal-300'
                        )}>
                          {fila.placa}
                        </span>
                      </td>

                      {/* Llegada estimada */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        <span className="text-sm tabular-nums text-gray-500 dark:text-slate-400">
                          {fila.horaEst ?? '—'}
                        </span>
                      </td>

                      {/* Llegada real */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        {fila.horaReal ? (
                          <span className="text-sm tabular-nums font-medium text-green-600 dark:text-green-400">
                            ✓ {fila.horaReal}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-300 dark:text-slate-600">—</span>
                        )}
                      </td>

                      {/* Estado */}
                      <td className="py-3 px-3">
                        {esIda ? (
                          <EstadoBadge estado={s.estado} />
                        ) : (
                          <EstadoBadge estado={s.hora_retorno_real ? 'COMPLETADO' : s.hora_salida_planta ? 'EN_CURSO' : 'PROGRAMADO'} />
                        )}
                      </td>

                      {/* Acciones — solo en filas de IDA */}
                      <td className="py-3 px-3">
                        {esIda && (
                          <div className="flex gap-1.5 flex-wrap">
                            {s.estado === 'PROGRAMADO' && (
                              <button onClick={() => mutacion.mutate({ id: s.servicio_id, estado: 'EN_CURSO' })}
                                className="text-xs px-2.5 py-1 rounded-md bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 hover:bg-green-200 font-medium whitespace-nowrap">
                                Iniciar
                              </button>
                            )}
                            {s.estado === 'EN_CURSO' && (
                              <button onClick={() => mutacion.mutate({ id: s.servicio_id, estado: 'COMPLETADO' })}
                                className="text-xs px-2.5 py-1 rounded-md bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 hover:bg-blue-200 font-medium whitespace-nowrap">
                                Completar
                              </button>
                            )}
                            {['PROGRAMADO', 'EN_CURSO'].includes(s.estado) && (
                              <button
                                onClick={() => confirm(`¿Cancelar el servicio de las ${fila.hora}?`) &&
                                  mutacion.mutate({ id: s.servicio_id, estado: 'CANCELADO' })}
                                className="text-xs px-2.5 py-1 rounded-md bg-red-50 dark:bg-red-900/40 text-red-500 dark:text-red-300 hover:bg-red-100 font-medium whitespace-nowrap">
                                Cancelar
                              </button>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
