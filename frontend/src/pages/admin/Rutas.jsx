import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../context/AuthContext'
import { getRutas } from '../../api/rutas'
import { Search } from 'lucide-react'
import clsx from 'clsx'

const TIPO_SERVICIO_COLORS = {
  PERSONAL:   'bg-blue-100 text-blue-800',
  MINAS:      'bg-amber-100 text-amber-800',
  MINERALES:  'bg-purple-100 text-purple-800',
}

export default function Rutas() {
  const { user } = useAuth()
  const [busqueda, setBusqueda] = useState('')
  const [filtroTipo, setFiltroTipo] = useState('')

  const { data: rutas = [], isLoading } = useQuery({
    queryKey: ['rutas', user?.sede_id],
    queryFn: () => getRutas({ sede_id: user.sede_id }),
    enabled: !!user?.sede_id,
  })

  const filtradas = rutas.filter(r => {
    const q = busqueda.toLowerCase()
    return (
      (!q || r.nombre?.toLowerCase().includes(q)) &&
      (!filtroTipo || r.tipo_servicio === filtroTipo)
    )
  })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Rutas</h1>
        <span className="text-sm text-gray-500">{filtradas.length} rutas activas</span>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Buscar ruta..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
        {['', 'PERSONAL', 'MINAS', 'MINERALES'].map(t => (
          <button
            key={t}
            onClick={() => setFiltroTipo(t)}
            className={clsx(
              'text-xs px-3 py-1.5 rounded-full font-medium transition-colors border',
              filtroTipo === t
                ? 'bg-brand-600 text-white border-brand-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-brand-300'
            )}
          >
            {t || 'Todas'}
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 border-b">
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Nombre</th>
                <th className="py-3 px-4">Tipo</th>
                <th className="py-3 px-4">T. estimado</th>
                <th className="py-3 px-4">2 conductores</th>
                <th className="py-3 px-4">Estado</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={6} className="text-center py-10 text-gray-400">Cargando...</td></tr>}
              {!isLoading && filtradas.length === 0 && <tr><td colSpan={6} className="text-center py-10 text-gray-400">Sin rutas</td></tr>}
              {filtradas.map(r => (
                <tr key={r.ruta_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-xs text-gray-400">#{r.ruta_id}</td>
                  <td className="py-3 px-4 text-sm font-medium text-gray-900">{r.nombre}</td>
                  <td className="py-3 px-4">
                    <span className={clsx('badge', TIPO_SERVICIO_COLORS[r.tipo_servicio] ?? 'bg-gray-100 text-gray-600')}>
                      {r.tipo_servicio}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {r.tiempo_estimado_min ? `${r.tiempo_estimado_min} min` : '—'}
                  </td>
                  <td className="py-3 px-4">
                    <span className={clsx('badge', r.requiere_dos_conductores ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500')}>
                      {r.requiere_dos_conductores ? 'Sí' : 'No'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={clsx('badge', r.activa ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500')}>
                      {r.activa ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
