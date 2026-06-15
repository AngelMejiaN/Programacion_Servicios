import api from './client'

export const getSedes = () =>
  api.get('/sedes/').then((r) => r.data)
