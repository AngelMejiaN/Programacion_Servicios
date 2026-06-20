import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { useAuth } from '../context/AuthContext'
import { getServicios, crearServicio, cambiarEstado, descargarPlantilla, importarServicios } from '../api/servicios'
import { getRutas, getRuta } from '../api/rutas'
import { getVehiculos } from '../api/vehiculos'
import { getConductores } from '../api/conductores'
import { getClientes } from '../api/clientes'
import { getSedes } from '../api/sedes'
import { EstadoBadge } from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import { Plus, Download, Upload, RefreshCw, ChevronLeft, ChevronRight, Clock, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

// ── Sección con borde de color ───────────────────────────────────────────────
function Seccion({ titulo, subtitulo, color = 'blue', children }) {
  const colors = {
    blue:  'bg-blue-50  dark:bg-blue-950  border-blue-200  dark:border-blue-800  text-blue-700  dark:text-blue-300',
    amber: 'bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300',
    teal:  'bg-teal-50  dark:bg-teal-950  border-teal-200  dark:border-teal-800  text-teal-700  dark:text-teal-300',
    green: 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300',
  }
  return (
    <div className="space-y-3">
      <div className={clsx('px-4 py-2 rounded-lg border', colors[color])}>
        <p className="text-sm font-semibold">{titulo}</p>
        {subtitulo && <p className="text-xs opacity-75 mt-0.5">{subtitulo}</p>}
      </div>
      {children}
    </div>
  )
}

// ── Formulario de nuevo servicio ─────────────────────────────────────────────
function FormServicio({ onClose }) {
  const { user } = useAuth()
  const qc = useQueryClient()

  // ── Estado del formulario ────────────────────────────────────────────────
  const [sedeId,          setSedeId]          = useState(String(user?.sede_id ?? ''))
  const [clienteId,       setClienteId]       = useState('')
  const [fecha,           setFecha]           = useState(format(new Date(), 'yyyy-MM-dd'))
  const [rutaId,          setRutaId]          = useState('')
  const [vehiculoId,      setVehiculoId]      = useState('')
  const [conductorId,     setConductorId]     = useState('')
  const [conductor2Id,    setConductor2Id]    = useState('')
  const [horaInicio,      setHoraInicio]      = useState('')
  const [horaFin,         setHoraFin]         = useState('')
  const [paraderoOrigenId,setParaderoOrigenId]= useState('')
  const [observaciones,   setObs]             = useState('')
  const [mismaUnidad,     setMismaUnidad]     = useState(true)
  const [retVehiculoId,   setRetVehiculoId]   = useState('')
  const [retConductorId,  setRetConductorId]  = useState('')
  const [horaSalidaPlanta,setHoraSalidaPlanta]= useState('')
  const [error,           setError]           = useState(null)

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: sedes = [] } = useQuery({
    queryKey: ['sedes'],
    queryFn: getSedes,
  })

  const { data: rutas = [], isFetching: loadingRutas } = useQuery({
    queryKey: ['rutas', sedeId],
    queryFn: () => getRutas({ sede_id: Number(sedeId) }),
    enabled: !!sedeId,
  })

  const rutaSelecBase = rutas.find(r => String(r.ruta_id) === rutaId)
  const { data: rutaDetalle } = useQuery({
    queryKey: ['ruta', rutaId],
    queryFn: () => getRuta(Number(rutaId)),
    enabled: !!rutaId && !!rutaSelecBase && !rutaSelecBase.origen_fijo,
  })

  const { data: vehiculos = [], isFetching: loadingVehiculos } = useQuery({
    queryKey: ['vehiculos', sedeId],
    queryFn: () => getVehiculos({ sede_id: Number(sedeId), operativo: true }),
    enabled: !!sedeId,
  })

  const { data: conductores = [], isFetching: loadingConductores, isError: condError } = useQuery({
    queryKey: ['conductores', sedeId],
    queryFn: () => getConductores(Number(sedeId)),
    enabled: !!sedeId,
  })

  const { data: todosClientes = [] } = useQuery({
    queryKey: ['clientes', sedeId],
    queryFn: () => getClientes(Number(sedeId)),
    enabled: !!sedeId,
  })

  // ── Datos derivados ──────────────────────────────────────────────────────
  const sede        = sedes.find(s => String(s.sede_id) === sedeId)
  const tipoSede    = sede?.tipo ?? 'A'
  const rutaSelec   = rutaDetalle ?? rutaSelecBase
  const requiereDos = rutaSelec?.requiere_dos_conductores
  const tiempoEst   = rutaSelec?.tiempo_estimado_min

  // Clientes de la sede — el backend ya los filtra con sede_id
  const clientesDeSede = todosClientes

  // Rutas filtradas por cliente (si se seleccionó uno)
  const rutasFiltradas = clienteId
    ? rutas.filter(r => String(r.cliente_id) === clienteId)
    : rutas

  // Hora llegada estimada (Tipo A)
  const horaLlegadaEst = (() => {
    if (tipoSede === 'A' && tiempoEst && horaInicio) {
      try {
        const [h, m] = horaInicio.split(':').map(Number)
        const total = h * 60 + m + tiempoEst
        return `${String(Math.floor(total / 60) % 24).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
      } catch { return null }
    }
    return null
  })()

  // ── Mutación guardar ─────────────────────────────────────────────────────
  const mutacion = useMutation({
    mutationFn: crearServicio,
    onSuccess: () => { qc.invalidateQueries(['servicios']); onClose() },
    onError: (e) => {
      const detail = e.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg).join(' | '))
      } else {
        setError(detail ?? e.message ?? 'Error al crear el servicio')
      }
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)

    if (!sedeId || !rutaId || !vehiculoId || !conductorId || !horaInicio) {
      setError('Completa todos los campos obligatorios (*).')
      return
    }

    mutacion.mutate({
      fecha,
      sede_id:            Number(sedeId),
      ruta_id:            Number(rutaId),
      vehiculo_id:        Number(vehiculoId),
      conductor_id:       Number(conductorId),
      conductor2_id:      conductor2Id  ? Number(conductor2Id) : null,
      hora_inicio:        horaInicio,
      hora_fin_manual:    horaFin       || null,
      paradero_origen_id: paraderoOrigenId ? Number(paraderoOrigenId) : null,
      observaciones:      observaciones  || null,
      retorno_misma_unidad: mismaUnidad,
      retorno_vehiculo_id:  !mismaUnidad && retVehiculoId  ? Number(retVehiculoId)  : null,
      retorno_conductor_id: !mismaUnidad && retConductorId ? Number(retConductorId) : null,
      hora_salida_planta: horaSalidaPlanta || null,
    })
  }

  const onChangeSede = (v) => {
    setSedeId(v)
    setRutaId('')
    setClienteId('')
    setVehiculoId('')
    setConductorId('')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">

      {/* ── DATOS GENERALES ─────────────────────────────────────────────── */}
      <Seccion titulo="Datos generales" subtitulo="Sede, fecha, vehículo y conductor" color="blue">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">
              Sede * {user?.rol !== 'administrador' && <span className="text-xs text-gray-400 font-normal">(solo admin puede cambiarla)</span>}
            </label>
            <select
              className="input"
              value={sedeId}
              onChange={e => onChangeSede(e.target.value)}
              required
              disabled={user?.rol !== 'administrador'}
            >
              <option value="">Seleccionar sede...</option>
              {sedes.map(s => (
                <option key={s.sede_id} value={String(s.sede_id)}>
                  {s.nombre} — Tipo {s.tipo}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Fecha *</label>
            <input type="date" className="input" value={fecha} onChange={e => setFecha(e.target.value)} required />
          </div>

          <div>
            <label className="label">Vehículo *</label>
            <select className="input" value={vehiculoId} onChange={e => setVehiculoId(e.target.value)} required disabled={!sedeId}>
              <option value="">{loadingVehiculos ? 'Cargando...' : 'Seleccionar vehículo...'}</option>
              {vehiculos.map(v => (
                <option key={v.vehiculo_id} value={String(v.vehiculo_id)}>
                  {v.placa} — {v.marca} {v.modelo}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Conductor 1 *</label>
            <select className="input" value={conductorId} onChange={e => setConductorId(e.target.value)} required disabled={!sedeId || condError}>
              <option value="">
                {loadingConductores ? 'Cargando...' : condError ? '⚠ Error — ver abajo' : 'Seleccionar conductor...'}
              </option>
              {conductores.map(c => (
                <option key={c.emp_id} value={String(c.emp_id)}>{c.nombre_completo}</option>
              ))}
            </select>
            {condError && (
              <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                <AlertCircle size={11} /> No se pudo conectar con T_EMPLEADOS
              </p>
            )}
          </div>
        </div>

        <div>
          <label className="label">Observaciones</label>
          <input className="input" placeholder="Notas opcionales..." value={observaciones} onChange={e => setObs(e.target.value)} />
        </div>
      </Seccion>

      {/* ── TRAMO DE IDA ────────────────────────────────────────────────── */}
      {tipoSede === 'A' && (
        <Seccion titulo="Tramo de ida · Lima" subtitulo="Ruta fija — llegada calculada automáticamente" color="blue">
          <div className="grid grid-cols-3 gap-3 items-end">
            <div>
              <label className="label">Cliente <span className="text-gray-400 font-normal text-xs">(filtro opcional)</span></label>
              <select className="input" value={clienteId} onChange={e => { setClienteId(e.target.value); setRutaId('') }}>
                <option value="">Todos los clientes</option>
                {clientesDeSede.map(c => (
                  <option key={c.cliente_id} value={String(c.cliente_id)}>{c.nombre}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Ruta *</label>
              <select className="input" value={rutaId} onChange={e => setRutaId(e.target.value)} required disabled={!sedeId}>
                <option value="">{loadingRutas ? 'Cargando...' : 'Seleccionar ruta...'}</option>
                {rutasFiltradas.map(r => (
                  <option key={r.ruta_id} value={String(r.ruta_id)}>{r.nombre}</option>
                ))}
              </select>
            </div>

            <div>
              {tiempoEst ? (
                <div className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg px-3 h-9">
                  <Clock size={13} /> {tiempoEst} min estimados
                </div>
              ) : <div />}
            </div>
          </div>

          {requiereDos && (
            <div>
              <label className="label">Conductor 2 * <span className="text-amber-600 text-xs">(ruta requiere 2 conductores)</span></label>
              <select className="input" value={conductor2Id} onChange={e => setConductor2Id(e.target.value)} required>
                <option value="">Seleccionar...</option>
                {conductores.filter(c => String(c.emp_id) !== conductorId).map(c => (
                  <option key={c.emp_id} value={String(c.emp_id)}>{c.nombre_completo}</option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Hora de salida *</label>
              <input type="time" className="input" value={horaInicio} onChange={e => setHoraInicio(e.target.value)} required />
            </div>
            <div>
              <label className="label">Hora llegada estimada</label>
              <input type="time" className={clsx('input', horaLlegadaEst && 'text-teal-600 dark:text-teal-300 font-semibold')}
                value={horaLlegadaEst ?? ''} readOnly placeholder="--:--" />
              {horaLlegadaEst && <p className="text-xs text-teal-600 dark:text-teal-400 mt-1">✓ Calculada automáticamente</p>}
            </div>
          </div>
        </Seccion>
      )}

      {tipoSede === 'B' && (
        <Seccion titulo="Tramo de ida · Pisco" subtitulo="Rutas mixtas" color="amber">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Ruta *</label>
              <select className="input" value={rutaId} onChange={e => { setRutaId(e.target.value); setParaderoOrigenId('') }} required>
                <option value="">Seleccionar ruta...</option>
                {rutas.map(r => <option key={r.ruta_id} value={String(r.ruta_id)}>{r.nombre}</option>)}
              </select>
            </div>
            {rutaSelec && !rutaSelec.origen_fijo && (
              <div>
                <label className="label">Paradero de origen *</label>
                <select className="input" value={paraderoOrigenId} onChange={e => setParaderoOrigenId(e.target.value)} required>
                  <option value="">Seleccionar paradero...</option>
                  {(rutaSelec.paraderos_disponibles ?? []).map(p => (
                    <option key={p.paradero_id} value={String(p.paradero_id)}>{p.nombre}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Hora de salida *</label>
              <input type="time" className="input" value={horaInicio} onChange={e => setHoraInicio(e.target.value)} required /></div>
            <div><label className="label">Hora de fin *</label>
              <input type="time" className="input" value={horaFin} onChange={e => setHoraFin(e.target.value)} required /></div>
          </div>
        </Seccion>
      )}

      {tipoSede === 'C' && (
        <Seccion titulo="Tramo de ida · Cañete" subtitulo="Combinación predefinida de origen y destino" color="teal">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Cliente <span className="text-gray-400 font-normal text-xs">(filtro opcional)</span></label>
              <select className="input" value={clienteId} onChange={e => { setClienteId(e.target.value); setRutaId('') }}>
                <option value="">Todos los clientes</option>
                {clientesDeSede.map(c => <option key={c.cliente_id} value={String(c.cliente_id)}>{c.nombre}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Combinación de ruta *</label>
              <select className="input" value={rutaId} onChange={e => setRutaId(e.target.value)} required>
                <option value="">Seleccionar...</option>
                {rutasFiltradas.map(r => <option key={r.ruta_id} value={String(r.ruta_id)}>{r.nombre}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Hora de inicio *</label>
              <input type="time" className="input" value={horaInicio} onChange={e => setHoraInicio(e.target.value)} required /></div>
            <div><label className="label">Hora de fin *</label>
              <input type="time" className="input" value={horaFin} onChange={e => setHoraFin(e.target.value)} required /></div>
          </div>
        </Seccion>
      )}

      {/* ── TRAMO DE RETORNO ────────────────────────────────────────────── */}
      <Seccion titulo="Tramo de retorno" subtitulo="Configura el viaje de regreso" color="green">
        <button type="button" onClick={() => setMismaUnidad(!mismaUnidad)}
          className={clsx('w-full flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-colors',
            mismaUnidad ? 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800'
                        : 'bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800'
          )}>
          <div className={clsx('w-5 h-5 rounded flex items-center justify-center shrink-0',
            mismaUnidad ? 'bg-green-500' : 'border-2 border-gray-300 dark:border-gray-600')}>
            {mismaUnidad && <svg width="11" height="11" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-800 dark:text-slate-200">
              {mismaUnidad ? 'Misma unidad y conductor' : 'Otra unidad o conductor'}
            </p>
            <p className="text-xs text-gray-500 dark:text-slate-400">
              {mismaUnidad ? 'Solo ingresa la hora de salida desde planta' : 'Selecciona vehículo y conductor para el retorno'}
            </p>
          </div>
        </button>

        {!mismaUnidad && (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Vehículo retorno *</label>
              <select className="input" value={retVehiculoId} onChange={e => setRetVehiculoId(e.target.value)} required>
                <option value="">Seleccionar...</option>
                {vehiculos.map(v => <option key={v.vehiculo_id} value={String(v.vehiculo_id)}>{v.placa} — {v.marca}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Conductor retorno *</label>
              <select className="input" value={retConductorId} onChange={e => setRetConductorId(e.target.value)} required>
                <option value="">Seleccionar...</option>
                {conductores.map(c => <option key={c.emp_id} value={String(c.emp_id)}>{c.nombre_completo}</option>)}
              </select>
            </div>
          </div>
        )}

        <div>
          <label className="label">Hora de salida desde planta</label>
          <input type="time" className="input" value={horaSalidaPlanta} onChange={e => setHoraSalidaPlanta(e.target.value)} />
        </div>
      </Seccion>

      {/* ── ERROR ─────────────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-start gap-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
          <AlertCircle size={16} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* ── BOTONES ───────────────────────────────────────────────────────── */}
      <div className="flex justify-end gap-3 pt-2 border-t border-gray-100 dark:border-slate-700">
        <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
        <button type="submit" className="btn-primary min-w-32 justify-center" disabled={mutacion.isPending}>
          {mutacion.isPending ? (
            <span className="flex items-center gap-2"><RefreshCw size={14} className="animate-spin" /> Guardando...</span>
          ) : 'Crear servicio'}
        </button>
      </div>
    </form>
  )
}

// ── Modal importación Excel ──────────────────────────────────────────────────
function ModalImportar({ defaultSedeId, open, onClose }) {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [archivo, setArchivo]   = useState(null)
  const [resultado, setResultado] = useState(null)
  const [sedeId, setSedeId]     = useState(String(defaultSedeId ?? ''))
  const [descargando, setDescargando] = useState(false)
  const [errorDescarga, setErrorDescarga] = useState(null)

  const { data: sedes = [] } = useQuery({ queryKey: ['sedes'], queryFn: getSedes })

  const mutacion = useMutation({
    mutationFn: (file) => importarServicios(Number(sedeId), file),
    onSuccess: (data) => { setResultado(data); qc.invalidateQueries(['servicios']) },
    onError: (e) => setErrorDescarga(e.response?.data?.detail ?? 'Error al importar'),
  })

  const handleDescargar = async () => {
    if (!sedeId) { setErrorDescarga('Selecciona una sede primero.'); return }
    setDescargando(true)
    setErrorDescarga(null)
    try {
      const blob = await descargarPlantilla(Number(sedeId))
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `plantilla_servicios_sede${sedeId}.xlsx`; a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setErrorDescarga('Error al descargar la plantilla. Verifica que el servidor esté activo.')
    } finally {
      setDescargando(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Importar servicios desde Excel">
      <div className="space-y-4">
        {/* Selector de sede */}
        <div>
          <label className="label">Sede *</label>
          <select
            className="input"
            value={sedeId}
            onChange={e => { setSedeId(e.target.value); setResultado(null) }}
            disabled={user?.rol !== 'administrador'}
          >
            <option value="">Seleccionar sede...</option>
            {sedes.map(s => (
              <option key={s.sede_id} value={String(s.sede_id)}>
                {s.nombre} — Tipo {s.tipo}
              </option>
            ))}
          </select>
          {user?.rol !== 'administrador' && (
            <p className="text-xs text-gray-400 mt-1">Solo administradores pueden cambiar la sede.</p>
          )}
        </div>

        {/* Instrucciones + descarga */}
        <div className="flex items-start gap-3 p-4 bg-brand-50 dark:bg-brand-950 rounded-lg border border-brand-100 dark:border-brand-800">
          <div className="flex-1 text-sm text-brand-800 dark:text-brand-300">
            <p className="font-medium mb-1">¿Cómo funciona?</p>
            <ol className="list-decimal list-inside space-y-1 text-brand-700 dark:text-brand-400 text-xs">
              <li>Descarga la plantilla con los datos de tu sede</li>
              <li>Completa las filas con los servicios</li>
              <li>Sube el archivo aquí</li>
            </ol>
          </div>
          <button onClick={handleDescargar} className="btn-secondary text-xs shrink-0" disabled={!sedeId || descargando}>
            <Download size={14} /> {descargando ? 'Descargando...' : 'Descargar plantilla'}
          </button>
        </div>

        {errorDescarga && (
          <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950 rounded-lg px-3 py-2 border border-red-200 dark:border-red-800">
            <AlertCircle size={14} /> {errorDescarga}
          </div>
        )}

        <div>
          <label className="label">Archivo Excel (.xlsx)</label>
          <input type="file" accept=".xlsx" className="input" onChange={e => { setArchivo(e.target.files[0]); setResultado(null) }} />
        </div>
        {resultado && (
          <div className={clsx('rounded-lg border p-4 text-sm',
            resultado.errores === 0 ? 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800'
                                    : 'bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800')}>
            <p className="font-semibold mb-2">✅ {resultado.creados} creados · ⚠ {resultado.errores} errores</p>
            {resultado.detalle.filter(d => d.estado === 'ERROR').map((d, i) => (
              <p key={i} className="text-red-600 dark:text-red-400 text-xs">Fila {d.fila}: {d.detalle}</p>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="btn-secondary">Cerrar</button>
          <button onClick={() => archivo && mutacion.mutate(archivo)} className="btn-primary" disabled={!archivo || mutacion.isPending}>
            {mutacion.isPending ? 'Importando...' : 'Importar'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ── Página principal ─────────────────────────────────────────────────────────
export default function Servicios() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [fecha, setFecha]             = useState(format(new Date(), 'yyyy-MM-dd'))
  const [modalNuevo, setModalNuevo]   = useState(false)
  const [modalImportar, setModalImportar] = useState(false)

  const { data: servicios = [], isLoading } = useQuery({
    queryKey: ['servicios', user?.sede_id, fecha],
    queryFn: () => getServicios(user.sede_id, fecha),
    enabled: !!user?.sede_id,
  })

  const mutCambiar = useMutation({
    mutationFn: ({ id, estado }) => cambiarEstado(id, estado),
    onSuccess: () => qc.invalidateQueries(['servicios']),
  })

  const cambiarFecha = (d) => {
    const dt = new Date(fecha + 'T12:00:00'); dt.setDate(dt.getDate() + d)
    setFecha(format(dt, 'yyyy-MM-dd'))
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Gestión de servicios</h1>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={() => cambiarFecha(-1)} className="btn-secondary px-2"><ChevronLeft size={16} /></button>
          <input type="date" className="input text-sm w-36" value={fecha} onChange={e => setFecha(e.target.value)} />
          <button onClick={() => cambiarFecha(1)} className="btn-secondary px-2"><ChevronRight size={16} /></button>
          <button onClick={() => setModalImportar(true)} className="btn-secondary gap-2"><Upload size={15} /> Importar Excel</button>
          <button onClick={() => setModalNuevo(true)} className="btn-primary gap-2"><Plus size={15} /> Nuevo servicio</button>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center items-center py-16 text-gray-400 dark:text-slate-500">
            <RefreshCw size={22} className="animate-spin mr-2" /> Cargando...
          </div>
        ) : servicios.length === 0 ? (
          <div className="text-center py-16 text-gray-400 dark:text-slate-500">
            <p className="font-medium">Sin servicios para {fecha}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  {['ID', 'Hora', 'Ruta', 'Vehículo', 'Estado', 'Acciones'].map(h => (
                    <th key={h} className="tbl-header">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {servicios.map(s => (
                  <tr key={s.servicio_id} className="tbl-row">
                    <td className="tbl-cell text-xs opacity-50">#{s.servicio_id}</td>
                    <td className="tbl-cell font-semibold">{s.hora_inicio?.slice(0,5) ?? '--:--'}</td>
                    <td className="tbl-cell">{s.ruta_nombre ?? `Ruta #${s.ruta_id}`}</td>
                    <td className="tbl-cell opacity-70">{s.vehiculo_placa ?? `#${s.vehiculo_id}`}</td>
                    <td className="tbl-cell"><EstadoBadge estado={s.estado} /></td>
                    <td className="tbl-cell">
                      <div className="flex gap-1 flex-wrap">
                        {s.estado === 'PROGRAMADO' && (
                          <button onClick={() => mutCambiar.mutate({ id: s.servicio_id, estado: 'EN_CURSO' })}
                            className="text-xs px-2 py-1 rounded bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-100 font-medium">Iniciar</button>
                        )}
                        {s.estado === 'EN_CURSO' && (
                          <button onClick={() => mutCambiar.mutate({ id: s.servicio_id, estado: 'COMPLETADO' })}
                            className="text-xs px-2 py-1 rounded bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-100 font-medium">Completar</button>
                        )}
                        {['PROGRAMADO','EN_CURSO'].includes(s.estado) && (
                          <button onClick={() => confirm('¿Cancelar este servicio?') && mutCambiar.mutate({ id: s.servicio_id, estado: 'CANCELADO' })}
                            className="text-xs px-2 py-1 rounded bg-red-50 dark:bg-red-900 text-red-600 dark:text-red-300 hover:bg-red-100 font-medium">Cancelar</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={modalNuevo} onClose={() => setModalNuevo(false)} title="Nuevo servicio" size="lg">
        <FormServicio onClose={() => setModalNuevo(false)} />
      </Modal>
      <ModalImportar defaultSedeId={user?.sede_id} open={modalImportar} onClose={() => setModalImportar(false)} />
    </div>
  )
}
