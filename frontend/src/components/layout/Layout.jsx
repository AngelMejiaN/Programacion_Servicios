import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Bus } from 'lucide-react'
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
          <div className="flex items-center gap-2">
            <div className="bg-brand-600 text-white rounded-lg p-1.5 shrink-0">
              <Bus size={18} />
            </div>
            <span className="font-bold text-brand-700 dark:text-brand-100 tracking-tight">TransitPro</span>
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
