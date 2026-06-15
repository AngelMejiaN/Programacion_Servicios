import api from './client'

export const getUsuarios = () =>
  api.get('/usuarios/').then((r) => r.data)

export const crearUsuario = (data) =>
  api.post('/usuarios/', data).then((r) => r.data)

export const actualizarUsuario = (id, data) =>
  api.patch(`/usuarios/${id}`, data).then((r) => r.data)

export const toggleUsuario = (id, activo) =>
  api.patch(`/usuarios/${id}/estado`, { activo }).then((r) => r.data)
