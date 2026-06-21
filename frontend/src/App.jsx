import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import Layout from './components/layout/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Calendario from './pages/Calendario'
import Servicios from './pages/Servicios'
import Vehiculos from './pages/admin/Vehiculos'
import Rutas from './pages/admin/Rutas'
import Usuarios from './pages/admin/Usuarios'
import Conductores from './pages/admin/Conductores'

function ProtectedRoute({ children, adminOnly = false }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && user.rol !== 'administrador') return <Navigate to="/" replace />
  return children
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="calendario" element={<Calendario />} />
        <Route path="servicios" element={<Servicios />} />
        <Route path="admin/vehiculos"   element={<ProtectedRoute adminOnly><Vehiculos /></ProtectedRoute>} />
        <Route path="admin/rutas"      element={<ProtectedRoute adminOnly><Rutas /></ProtectedRoute>} />
        <Route path="admin/usuarios"   element={<ProtectedRoute adminOnly><Usuarios /></ProtectedRoute>} />
        <Route path="admin/conductores" element={<ProtectedRoute adminOnly><Conductores /></ProtectedRoute>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
