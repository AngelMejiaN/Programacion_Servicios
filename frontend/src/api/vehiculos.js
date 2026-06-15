import api from './client'

export const getVehiculos = (params) =>
  api.get('/vehiculos/', { params }).then((r) => r.data)

export const crearVehiculo = (data) =>
  api.post('/vehiculos/', data).then((r) => r.data)

export const actualizarVehiculo = (id, data) =>
  api.patch(`/vehiculos/${id}`, data).then((r) => r.data)
