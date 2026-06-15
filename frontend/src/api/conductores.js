import api from './client'

export const getConductores = (sedeId) =>
  api.get('/conductores/', { params: { sede_id: sedeId } }).then((r) => r.data)
