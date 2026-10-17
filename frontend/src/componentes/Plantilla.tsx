import { NavLink, Outlet } from 'react-router-dom'

/** Estructura común: encabezado, navegación y contenido. Los módulos añaden sus enlaces. */
export function Plantilla() {
  return (
    <div className="plantilla">
      <header className="encabezado">
        <span className="marca">Apartaestudios</span>
        <nav aria-label="Navegación principal">
          <NavLink to="/" end>
            Inicio
          </NavLink>
        </nav>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  )
}
