import api from './client'

export const getRutas = (params) =>
  api.get('/rutas/', { params }).then((r) => r.data)

export const getRuta = (id) =>
  api.get(`/rutas/${id}`).then((r) => r.data)
