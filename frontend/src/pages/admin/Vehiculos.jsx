import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../context/AuthContext'
import { getVehiculos, crearVehiculo, actualizarVehiculo } from '../../api/vehiculos'
import Modal from '../../components/ui/Modal'
import { Plus, Search, Truck } from 'lucide-react'
import clsx from 'clsx'

const TIPOS = ['MINIBUS', 'BUS', 'CAMIONETA', 'VAN', 'OTRO']

function FormVehiculo({ sedeId, vehiculo, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState(vehiculo ?? {
    placa: '', marca: '', modelo: '', anio: '', tipo: 'MINIBUS',
    color: '', sede_id: sedeId, operativo: true,
  })
  const [error, setError] = useState(null)

  const esNuevo = !vehiculo
  const mutacion = useMutation({
    mutationFn: esNuevo
      ? (d) => crearVehiculo(d)
      : (d) => actualizarVehiculo(vehiculo.vehiculo_id, d),
    onSuccess: () => { qc.invalidateQueries(['vehiculos']); onClose() },
    onError: (e) => setError(e.response?.data?.detail ?? 'Error'),
  })

  const set = (k) => (e) => setForm(f => ({
    ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value
  }))

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutacion.mutate(form) }} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Placa *</label>
          <input className="input uppercase" value={form.placa} onChange={set('placa')} required placeholder="ABC-123" />
        </div>
        <div>
          <label className="label">Tipo *</label>
          <select className="input" value={form.tipo} onChange={set('tipo')} required>
            {TIPOS.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Marca</label>
          <input className="input" value={form.marca} onChange={set('marca')} placeholder="Mercedes, Toyota..." />
        </div>
        <div>
          <label className="label">Modelo</label>
          <input className="input" value={form.modelo} onChange={set('modelo')} placeholder="Sprinter, Hiace..." />
        </div>
        <div>
          <label className="label">Año</label>
          <input className="input" type="number" min="2000" max="2030" value={form.anio} onChange={set('anio')} />
        </div>
        <div>
          <label className="label">Color</label>
          <input className="input" value={form.color ?? ''} onChange={set('color')} />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <input id="operativo" type="checkbox" checked={form.operativo} onChange={set('operativo')} className="rounded" />
        <label htmlFor="operativo" className="text-sm text-gray-700">Vehículo operativo</label>
      </div>
      {error && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
        <button type="submit" className="btn-primary" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Guardando...' : (esNuevo ? 'Crear vehículo' : 'Guardar cambios')}
        </button>
      </div>
    </form>
  )
}

export default function Vehiculos() {
  const { user } = useAuth()
  const [busqueda, setBusqueda] = useState('')
  const [soloOperativos, setSoloOperativos] = useState(false)
  const [modal, setModal] = useState(null)  // null | 'nuevo' | vehiculo

  const { data: vehiculos = [], isLoading } = useQuery({
    queryKey: ['vehiculos', user?.sede_id],
    queryFn: () => getVehiculos({ sede_id: user.sede_id }),
    enabled: !!user?.sede_id,
  })

  const filtrados = vehiculos.filter(v => {
    const q = busqueda.toLowerCase()
    const match = !q || v.placa?.toLowerCase().includes(q) || v.marca?.toLowerCase().includes(q) || v.modelo?.toLowerCase().includes(q)
    return match && (!soloOperativos || v.operativo)
  })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Vehículos</h1>
        <button onClick={() => setModal('nuevo')} className="btn-primary gap-2">
          <Plus size={15} /> Agregar vehículo
        </button>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Buscar por placa, marca..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
          <input type="checkbox" checked={soloOperativos} onChange={(e) => setSoloOperativos(e.target.checked)} className="rounded" />
          Solo operativos
        </label>
        <span className="text-sm text-gray-500">{filtrados.length} vehículos</span>
      </div>

      {/* Tabla */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 border-b">
                <th className="py-3 px-4">Placa</th>
                <th className="py-3 px-4">Marca / Modelo</th>
                <th className="py-3 px-4">Tipo</th>
                <th className="py-3 px-4">Año</th>
                <th className="py-3 px-4">Color</th>
                <th className="py-3 px-4">Estado</th>
                <th className="py-3 px-4">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={7} className="text-center py-10 text-gray-400">Cargando...</td></tr>
              )}
              {!isLoading && filtrados.length === 0 && (
                <tr><td colSpan={7} className="text-center py-10 text-gray-400">Sin vehículos</td></tr>
              )}
              {filtrados.map(v => (
                <tr key={v.vehiculo_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-semibold text-sm">{v.placa}</td>
                  <td className="py-3 px-4 text-sm">{v.marca} {v.modelo}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">{v.tipo}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">{v.anio ?? '—'}</td>
                  <td className="py-3 px-4 text-sm text-gray-600">{v.color ?? '—'}</td>
                  <td className="py-3 px-4">
                    <span className={clsx('badge', v.operativo ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500')}>
                      {v.operativo ? 'Operativo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => setModal(v)}
                      className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600 hover:bg-gray-200 font-medium"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        open={!!modal}
        onClose={() => setModal(null)}
        title={modal === 'nuevo' ? 'Nuevo vehículo' : `Editar — ${modal?.placa}`}
        size="md"
      >
        {modal && (
          <FormVehiculo
            sedeId={user?.sede_id}
            vehiculo={modal === 'nuevo' ? null : modal}
            onClose={() => setModal(null)}
          />
        )}
      </Modal>
    </div>
  )
}
