import clsx from 'clsx'

const ESTADO_STYLES = {
  PROGRAMADO: 'bg-yellow-100 text-yellow-800',
  EN_CURSO:   'bg-green-100  text-green-800',
  COMPLETADO: 'bg-blue-100   text-blue-800',
  CANCELADO:  'bg-red-100    text-red-700',
}

const ESTADO_LABELS = {
  PROGRAMADO: 'Programado',
  EN_CURSO:   'En curso',
  COMPLETADO: 'Completado',
  CANCELADO:  'Cancelado',
}

export function EstadoBadge({ estado }) {
  return (
    <span className={clsx('badge', ESTADO_STYLES[estado] ?? 'bg-gray-100 text-gray-700')}>
      {ESTADO_LABELS[estado] ?? estado}
    </span>
  )
}

export function RolBadge({ rol }) {
  const styles = {
    administrador: 'bg-purple-100 text-purple-800',
    programador:   'bg-brand-100  text-brand-800',
    supervisor:    'bg-orange-100 text-orange-700',
    conductor:     'bg-gray-100   text-gray-700',
  }
  return (
    <span className={clsx('badge', styles[rol] ?? 'bg-gray-100 text-gray-700')}>
      {rol}
    </span>
  )
}
