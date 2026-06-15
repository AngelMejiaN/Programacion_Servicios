import api from './client'

export const getClientes = (sedeId) =>
  api.get('/clientes/', { params: sedeId ? { sede_id: sedeId } : {} }).then((r) => r.data)
