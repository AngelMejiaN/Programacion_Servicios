import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Sidebar from './Sidebar'

const PAGE_TITLES = {
  '/':               'Dashboard',
  '/calendario':     'Calendario semanal',
  '/servicios':      'Gestión de servicios',
  '/admin/vehiculos':'Vehículos',
  '/admin/rutas':    'Rutas',
  '/admin/usuarios': 'Usuarios',
}

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const { user }    = useAuth()
  const location    = useLocation()
  const titulo      = PAGE_TITLES[location.pathname] ?? 'TransitPro'

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-slate-900">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center justify-between px-6 py-3 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 shrink-0 shadow-sm">
          <h1 className="text-base font-semibold text-gray-800 dark:text-slate-100">{titulo}</h1>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold">
              {user?.nombre?.[0]?.toUpperCase()}
            </div>
            <div className="text-sm">
              <span className="font-medium text-gray-800 dark:text-slate-100">{user?.nombre}</span>
              <span className="text-gray-400 dark:text-slate-500 capitalize text-xs ml-1">· {user?.rol}</span>
            </div>
          </div>
        </header>

        {/* Contenido */}
        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-slate-900">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
