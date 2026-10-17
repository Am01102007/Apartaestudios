import { Link } from 'react-router-dom'

export function NoEncontrada() {
  return (
    <section>
      <h1>Página no encontrada</h1>
      <Link to="/">Volver al inicio</Link>
    </section>
  )
}
