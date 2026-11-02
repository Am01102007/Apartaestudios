import { UsuarioActual } from '../api/tipos';

/**
 * Acciones que la pantalla muestra u oculta según el rol. Sigue la tabla de roles de la propuesta
 * (sección 4), con un cambio decidido el 2 de noviembre: el empleado también registra y edita
 * residentes. La pantalla solo oculta los botones; quien autoriza es el servidor.
 */
export type AccionAdministrativa =
  | 'gestionar_propietarios'
  | 'gestionar_apartaestudios'
  | 'gestionar_residentes'
  | 'gestionar_bloqueos'
  | 'anular_contratos';

export function puede(usuario: UsuarioActual | null, accion: AccionAdministrativa): boolean {
  if (!usuario) return false;
  if (accion === 'gestionar_residentes') return true;
  return usuario.rol === 'administrador';
}
