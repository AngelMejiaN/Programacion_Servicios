import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(() => {
    try { return JSON.parse(localStorage.getItem('bs_user')) } catch { return null }
  })
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const login = async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiLogin(email, password)
      localStorage.setItem('bs_token', data.access_token)
      localStorage.setItem('bs_user', JSON.stringify({
        id:      data.usuario_id,
        nombre:  data.nombre,
        rol:     data.rol,
        sede_id: data.sede_id,
      }))
      setUser({ id: data.usuario_id, nombre: data.nombre, rol: data.rol, sede_id: data.sede_id })
      return true
    } catch (e) {
      setError(e.response?.data?.detail || 'Error al iniciar sesión')
      return false
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('bs_token')
    localStorage.removeItem('bs_user')
    setUser(null)
  }

  const isAdmin = user?.rol === 'administrador'
  const isProgramador = ['administrador', 'programador'].includes(user?.rol)

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, isAdmin, isProgramador }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
