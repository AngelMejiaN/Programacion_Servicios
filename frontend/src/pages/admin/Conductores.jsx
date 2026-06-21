import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../context/AuthContext'
import { getConductores, crearConductor, actualizarConductor } from '../../api/conductores'
import Modal from '../../components/ui/Modal'
import { Plus, Search, Pencil } from 'lucide-react'
import clsx from 'clsx'

const CATEGORIAS = ['AI', 'AII', 'AIII', 'BII', 'BIII']

function FormConductor({ sedeId, conductor, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState(conductor ?? {
    nombre_completo: '', licencia: '', licencia_cat: 'AIII', telefono: '', sede_id: sedeId,
  })
  const [error, setError] = useState(null)

  const esNuevo = !conductor
  const mutacion = useMutation({
    mutationFn: esNuevo
      ? (d) => crearConductor(d)
      : (d) => actualizarConductor(conductor.emp_id, d),
    onSuccess: () => { qc.invalidateQueries(['conductores']); onClose() },
    onError: (e) => setError(e.response?.data?.detail ?? 'Error al guardar'),
  })

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutacion.mutate(form) }} className="space-y-4">
      <div>
        <label className="label">Nombre completo *</label>
        <input
          className="input uppercase"
          value={form.nombre_completo}
          onChange={set('nombre_completo')}
          required
          placeholder="APELLIDOS, Nombre"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">N° de licencia</label>
          <input className="input" value={form.licencia ?? ''} onChange={set('licencia')} placeholder="Q03-12345" />
        </div>
        <div>
          <label className="label">Categoría</label>
          <select className="input" value={form.licencia_cat ?? ''} onChange={set('licencia_cat')}>
            <option value="">—</option>
            {CATEGORIAS.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
      </div>
      <div>
        <label className="label">Teléfono</label>
        <input className="input" value={form.telefono ?? ''} onChange={set('telefono')} placeholder="9XX XXX XXX" />
      </div>
      {error && <p className="text-sm text-red-600 bg-red-50 dark:bg-red-950 rounded-lg px-3 py-2">{error}</p>}
      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
        <button type="submit" className="btn-primary" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Guardando...' : (esNuevo ? 'Crear conductor' : 'Guardar cambios')}
        </button>
      </div>
    </form>
  )
}

export default function Conductores() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [busqueda, setBusqueda]   = useState('')
  const [soloActivos, setSoloActivos] = useState(true)
  const [modal, setModal]         = useState(null)  // null | 'nuevo' | conductor

  const { data: conductores = [], isLoading } = useQuery({
    queryKey: ['conductores', user?.sede_id, 'admin'],
    queryFn: () => getConductores(user?.sede_id, true),
    enabled: !!user?.sede_id,
  })

  const mutToggle = useMutation({
    mutationFn: (c) => actualizarConductor(c.emp_id, { activo: !c.activo }),
    onSuccess: () => qc.invalidateQueries(['conductores']),
  })

  const filtrados = conductores.filter(c => {
    const q = busqueda.toLowerCase()
    const match = !q || c.nombre_completo?.toLowerCase().includes(q) || c.licencia?.toLowerCase().includes(q)
    return match && (!soloActivos || c.activo)
  })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Conductores</h1>
        <button onClick={() => setModal('nuevo')} className="btn-primary gap-2">
          <Plus size={15} /> Agregar conductor
        </button>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Buscar por nombre o licencia..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={soloActivos}
            onChange={(e) => setSoloActivos(e.target.checked)}
            className="rounded"
          />
          Solo activos
        </label>
        <span className="text-sm text-gray-500 dark:text-slate-400">{filtrados.length} conductores</span>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                {['Nombre', 'Licencia', 'Categoría', 'Teléfono', 'Estado', 'Acciones'].map(h => (
                  <th key={h} className="tbl-header">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={6} className="text-center py-10 text-gray-400">Cargando...</td></tr>
              )}
              {!isLoading && filtrados.length === 0 && (
                <tr><td colSpan={6} className="text-center py-10 text-gray-400">Sin conductores</td></tr>
              )}
              {filtrados.map(c => (
                <tr key={c.emp_id} className="tbl-row">
                  <td className="tbl-cell font-medium">{c.nombre_completo}</td>
                  <td className="tbl-cell font-mono text-sm">{c.licencia ?? '—'}</td>
                  <td className="tbl-cell">
                    {c.licencia_cat
                      ? <span className="badge bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300">{c.licencia_cat}</span>
                      : <span className="tbl-cell opacity-40">—</span>
                    }
                  </td>
                  <td className="tbl-cell text-gray-600 dark:text-slate-400">{c.telefono || '—'}</td>
                  <td className="tbl-cell">
                    <span className={clsx('badge', c.activo
                      ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300'
                      : 'bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-slate-400'
                    )}>
                      {c.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="tbl-cell">
                    <div className="flex gap-1">
                      <button
                        onClick={() => setModal(c)}
                        className="text-xs px-2 py-1 rounded bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-100 font-medium flex items-center gap-1"
                      >
                        <Pencil size={11} /> Editar
                      </button>
                      <button
                        onClick={() => mutToggle.mutate(c)}
                        disabled={mutToggle.isPending}
                        className={clsx('text-xs px-2 py-1 rounded font-medium transition-colors',
                          c.activo
                            ? 'bg-red-50 dark:bg-red-900 text-red-600 dark:text-red-300 hover:bg-red-100'
                            : 'bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-100'
                        )}
                      >
                        {c.activo ? 'Desactivar' : 'Activar'}
                      </button>
                    </div>
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
        title={modal === 'nuevo' ? 'Nuevo conductor' : `Editar — ${modal?.nombre_completo}`}
        size="md"
      >
        {modal && (
          <FormConductor
            sedeId={user?.sede_id}
            conductor={modal === 'nuevo' ? null : modal}
            onClose={() => setModal(null)}
          />
        )}
      </Modal>
    </div>
  )
}
