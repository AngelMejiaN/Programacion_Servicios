import api from './client'

export const getConductores = (sedeId, incluirInactivos = false) =>
  api.get('/conductores/', { params: { sede_id: sedeId, incluir_inactivos: incluirInactivos } }).then(r => r.data)

export const crearConductor = (data) =>
  api.post('/conductores/', data).then(r => r.data)

export const actualizarConductor = (empId, data) =>
  api.patch(`/conductores/${empId}`, data).then(r => r.data)
