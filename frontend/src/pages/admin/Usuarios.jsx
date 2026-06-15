import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../context/AuthContext'
import { getUsuarios, crearUsuario, actualizarUsuario, toggleUsuario } from '../../api/usuarios'
import { RolBadge } from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import { Plus, Search, Pencil } from 'lucide-react'
import clsx from 'clsx'

const ROLES = ['administrador', 'programador', 'supervisor']

// ── Formulario crear usuario ─────────────────────────────────────────────────
function FormNuevoUsuario({ onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ nombre: '', email: '', password: '', rol: 'programador', sede_id: '' })
  const [error, setError] = useState(null)

  const mutacion = useMutation({
    mutationFn: crearUsuario,
    onSuccess: () => { qc.invalidateQueries(['usuarios']); onClose() },
    onError: (e) => setError(e.response?.data?.detail ?? 'Error al crear usuario'),
  })

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutacion.mutate(form) }} className="space-y-4">
      <div>
        <label className="label">Nombre completo *</label>
        <input className="input" value={form.nombre} onChange={set('nombre')} required placeholder="Juan Pérez" />
      </div>
      <div>
        <label className="label">Correo electrónico *</label>
        <input className="input" type="email" value={form.email} onChange={set('email')} required placeholder="juan@empresa.com" />
      </div>
      <div>
        <label className="label">Contraseña inicial *</label>
        <input className="input" type="password" value={form.password} onChange={set('password')} required minLength={6} placeholder="Mínimo 6 caracteres" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Rol *</label>
          <select className="input" value={form.rol} onChange={set('rol')} required>
            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        <div>
          <label className="label">ID Sede</label>
          <input className="input" type="number" value={form.sede_id} onChange={set('sede_id')} placeholder="1, 2, 3..." />
        </div>
      </div>
      <div className="bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg px-4 py-3 text-xs text-amber-700 dark:text-amber-300">
        ⚠ El usuario deberá cambiar su contraseña en el primer inicio de sesión.
      </div>
      {error && <p className="text-sm text-red-600 bg-red-50 dark:bg-red-950 rounded-lg px-3 py-2">{error}</p>}
      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
        <button type="submit" className="btn-primary" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Creando...' : 'Crear usuario'}
        </button>
      </div>
    </form>
  )
}

// ── Formulario editar usuario ─────────────────────────────────────────────────
function FormEditarUsuario({ usuario, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    nombre:      usuario.nombre      ?? '',
    email:       usuario.email       ?? '',
    telegram_id: usuario.telegram_id ?? '',
    rol:         usuario.rol         ?? 'programador',
    sede_id:     usuario.sede_id     ?? '',
    password:    '',
  })
  const [error, setError] = useState(null)

  const mutacion = useMutation({
    mutationFn: (data) => actualizarUsuario(usuario.usuario_id, data),
    onSuccess: () => { qc.invalidateQueries(['usuarios']); onClose() },
    onError: (e) => setError(e.response?.data?.detail ?? 'Error al actualizar'),
  })

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {}
    if (form.nombre)      payload.nombre      = form.nombre
    if (form.email)       payload.email       = form.email
    if (form.telegram_id) payload.telegram_id = Number(form.telegram_id)
    if (form.rol)         payload.rol         = form.rol
    if (form.sede_id)     payload.sede_id     = Number(form.sede_id)
    if (form.password)    payload.password    = form.password
    mutacion.mutate(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">Nombre completo</label>
        <input className="input" value={form.nombre} onChange={set('nombre')} />
      </div>
      <div>
        <label className="label">Correo electrónico</label>
        <input className="input" type="email" value={form.email} onChange={set('email')} />
      </div>

      {/* Campo principal para vincular Telegram */}
      <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <label className="block text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">
          🔗 ID de Telegram
        </label>
        <input
          className="input"
          type="number"
          value={form.telegram_id}
          onChange={set('telegram_id')}
          placeholder="Ej: 123456789"
        />
        <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
          Para obtener tu ID, escríbele a <strong>@userinfobot</strong> en Telegram y copia el número que te responde.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Rol</label>
          <select className="input" value={form.rol} onChange={set('rol')}>
            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        <div>
          <label className="label">ID Sede</label>
          <input className="input" type="number" value={form.sede_id} onChange={set('sede_id')} placeholder="1, 2, 3..." />
        </div>
      </div>

      <div>
        <label className="label">Nueva contraseña <span className="text-gray-400 font-normal">(dejar vacío para no cambiar)</span></label>
        <input className="input" type="password" value={form.password} onChange={set('password')} minLength={6} placeholder="Solo si deseas cambiarla" />
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 dark:bg-red-950 rounded-lg px-3 py-2">{error}</p>}
      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onClose} className="btn-secondary">Cancelar</button>
        <button type="submit" className="btn-primary" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Guardando...' : 'Guardar cambios'}
        </button>
      </div>
    </form>
  )
}

// ── Página principal ─────────────────────────────────────────────────────────
export default function Usuarios() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [busqueda, setBusqueda]     = useState('')
  const [modalNuevo, setModalNuevo] = useState(false)
  const [editando, setEditando]     = useState(null)   // usuario a editar

  const { data: usuarios = [], isLoading } = useQuery({
    queryKey: ['usuarios'],
    queryFn: getUsuarios,
    enabled: user?.rol === 'administrador',
  })

  const mutToggle = useMutation({
    mutationFn: ({ id, activo }) => toggleUsuario(id, activo),
    onSuccess: () => qc.invalidateQueries(['usuarios']),
  })

  const filtrados = usuarios.filter(u => {
    const q = busqueda.toLowerCase()
    return !q || u.nombre?.toLowerCase().includes(q) || u.email?.toLowerCase().includes(q)
  })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Usuarios del sistema</h1>
        <button onClick={() => setModalNuevo(true)} className="btn-primary gap-2">
          <Plus size={15} /> Nuevo usuario
        </button>
      </div>

      <div className="relative max-w-xs">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input className="input pl-9" placeholder="Buscar usuario..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr>
              {['Nombre', 'Email', 'Rol', 'Sede', 'Telegram', 'Estado', 'Acciones'].map(h => (
                <th key={h} className="tbl-header">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={7} className="text-center py-10 text-gray-400">Cargando...</td></tr>}
            {!isLoading && filtrados.length === 0 && <tr><td colSpan={7} className="text-center py-10 text-gray-400">Sin usuarios</td></tr>}
            {filtrados.map(u => (
              <tr key={u.usuario_id} className="tbl-row">
                <td className="tbl-cell font-medium">{u.nombre}</td>
                <td className="tbl-cell opacity-60 text-xs">{u.email ?? '—'}</td>
                <td className="tbl-cell"><RolBadge rol={u.rol} /></td>
                <td className="tbl-cell">{u.sede_id ?? '—'}</td>
                <td className="tbl-cell">
                  {u.telegram_id
                    ? <span className="badge bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300">✓ {u.telegram_id}</span>
                    : <span className="badge bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-slate-400">No vinculado</span>
                  }
                </td>
                <td className="tbl-cell">
                  <span className={clsx('badge', u.activo ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300' : 'bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-slate-400')}>
                    {u.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="tbl-cell">
                  <div className="flex gap-1">
                    <button
                      onClick={() => setEditando(u)}
                      className="text-xs px-2 py-1 rounded bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-100 font-medium flex items-center gap-1"
                    >
                      <Pencil size={11} /> Editar
                    </button>
                    {u.usuario_id !== user?.id && (
                      <button
                        onClick={() => mutToggle.mutate({ id: u.usuario_id, activo: !u.activo })}
                        className={clsx('text-xs px-2 py-1 rounded font-medium transition-colors',
                          u.activo
                            ? 'bg-red-50 dark:bg-red-900 text-red-600 dark:text-red-300 hover:bg-red-100'
                            : 'bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-100'
                        )}
                      >
                        {u.activo ? 'Desactivar' : 'Activar'}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal open={modalNuevo} onClose={() => setModalNuevo(false)} title="Nuevo usuario">
        <FormNuevoUsuario onClose={() => setModalNuevo(false)} />
      </Modal>

      <Modal open={!!editando} onClose={() => setEditando(null)} title={`Editar — ${editando?.nombre}`}>
        {editando && <FormEditarUsuario usuario={editando} onClose={() => setEditando(null)} />}
      </Modal>
    </div>
  )
}
