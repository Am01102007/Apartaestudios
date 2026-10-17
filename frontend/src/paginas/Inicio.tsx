import { useQuery } from '@tanstack/react-query'
import { consultarSalud } from '../api/salud'

export function Inicio() {
  const { data, isPending, isError } = useQuery({ queryKey: ['salud'], queryFn: consultarSalud })

  let estado = 'Comprobando conexión con el servidor…'
  if (isError) estado = 'No hay conexión con el servidor.'
  else if (data?.base_de_datos === 'ok') estado = 'Servidor y base de datos disponibles.'
  else if (data) estado = 'El servidor responde, pero la base de datos no está disponible.'

  return (
    <section>
      <h1>Sistema de administración de apartaestudios</h1>
      <p role="status" aria-busy={isPending}>
        {estado}
      </p>
    </section>
  )
}
