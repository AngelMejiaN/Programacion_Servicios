import axios from 'axios'

// En desarrollo se usa el proxy de Vite ('/api' → localhost:8001).
// En producción se define VITE_API_URL con la URL pública del backend.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Inyectar token JWT en cada request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bs_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirigir a login si el token expira
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('bs_token')
      localStorage.removeItem('bs_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
