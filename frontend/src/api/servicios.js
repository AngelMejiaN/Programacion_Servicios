import api from './client'

export const getServicios = (sedeId, fecha, estado) =>
  api.get('/servicios/', { params: { sede_id: sedeId, fecha, estado } }).then((r) => r.data)

export const getServicio = (id) =>
  api.get(`/servicios/${id}`).then((r) => r.data)

export const crearServicio = (data) =>
  api.post('/servicios/', data).then((r) => r.data)

export const actualizarServicio = (id, data) =>
  api.patch(`/servicios/${id}`, data).then((r) => r.data)

export const cambiarEstado = (id, estado, observaciones) =>
  api.patch(`/servicios/${id}/estado`, { estado, observaciones }).then((r) => r.data)

export const cancelarServicio = (id, motivo) =>
  api.delete(`/servicios/${id}`, { params: { motivo } }).then((r) => r.data)

export const descargarPlantilla = (sedeId) =>
  api.get('/servicios/plantilla', {
    params: { sede_id: sedeId },
    responseType: 'blob',
  }).then((r) => r.data)

export const importarServicios = (sedeId, archivo) => {
  const form = new FormData()
  form.append('archivo', archivo)
  return api.post('/servicios/importar', form, {
    params: { sede_id: sedeId },
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}
