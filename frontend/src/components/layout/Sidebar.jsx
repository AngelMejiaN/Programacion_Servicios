import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useTheme } from '../../context/ThemeContext'
import {
  Menu, LayoutDashboard, Calendar, ClipboardList,
  Truck, Route, Users, LogOut, ChevronRight, Sun, Moon,
} from 'lucide-react'
import clsx from 'clsx'

const NAV_ITEMS = [
  { to: '/',           label: 'Dashboard',    icon: LayoutDashboard, roles: ['administrador','programador','supervisor'] },
  { to: '/calendario', label: 'Calendario',   icon: Calendar,        roles: ['administrador','programador','supervisor'] },
  { to: '/servicios',  label: 'Servicios',    icon: ClipboardList,   roles: ['administrador','programador'] },
  { divider: true, label: 'Administración', roles: ['administrador'] },
  { to: '/admin/vehiculos', label: 'Vehículos', icon: Truck,  roles: ['administrador'] },
  { to: '/admin/rutas',     label: 'Rutas',     icon: Route,  roles: ['administrador'] },
  { to: '/admin/usuarios',  label: 'Usuarios',  icon: Users,  roles: ['administrador'] },
]

export default function Sidebar({ collapsed, onToggle }) {
  const { user, logout }     = useAuth()
  const { dark, toggle }     = useTheme()

  const visibleItems = NAV_ITEMS.filter(
    item => !item.roles || item.roles.includes(user?.rol)
  )

  return (
    <aside className={clsx(
      'h-screen flex flex-col transition-all duration-200 shrink-0',
      'bg-brand-900 text-white',
      collapsed ? 'w-16' : 'w-56'
    )}>
      {/* Header */}
      {collapsed ? (
        <div className="flex items-center justify-center px-2 py-4 border-b border-white/10">
          <button
            onClick={onToggle}
            title="Expandir menú"
            className="text-white/60 hover:text-white transition-colors"
          >
            <Menu size={20} />
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-white/40 uppercase tracking-widest font-semibold leading-none mb-0.5">Rol</p>
            <p className="text-sm font-bold text-white capitalize truncate">{user?.rol}</p>
          </div>
          <button
            onClick={onToggle}
            title="Colapsar menú"
            className="text-white/40 hover:text-white transition-colors shrink-0"
          >
            <ChevronRight size={15} className="rotate-180" />
          </button>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {visibleItems.map((item, i) => {
          if (item.divider) {
            return !collapsed
              ? <p key={i} className="text-xs text-white/30 font-semibold uppercase tracking-wider px-3 pt-4 pb-1">{item.label}</p>
              : <hr key={i} className="border-white/10 my-2 mx-3" />
          }
          const Icon = item.icon
          return (
            <NavLink key={item.to} to={item.to} end={item.to === '/'}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-white/15 text-white'
                  : 'text-white/60 hover:bg-white/10 hover:text-white'
              )}>
              <Icon size={17} className="shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-white/10 px-2 py-3 space-y-1">
        {/* Toggle dark/light */}
        <button
          onClick={toggle}
          title={dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors text-white/60 hover:bg-white/10 hover:text-white"
        >
          {dark
            ? <Sun size={17} className="shrink-0" />
            : <Moon size={17} className="shrink-0" />
          }
          {!collapsed && (
            <span>{dark ? 'Modo claro' : 'Modo oscuro'}</span>
          )}
        </button>

        {/* Logout */}
        <button
          onClick={logout}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors text-white/60 hover:bg-white/10 hover:text-white"
        >
          <LogOut size={17} className="shrink-0" />
          {!collapsed && 'Cerrar sesión'}
        </button>
      </div>
    </aside>
  )
}
