import { UsuarioActual } from '../api/tipos';

/**
 * Acciones que el servidor reserva al administrador (tabla de roles de la propuesta, sección 4).
 * La pantalla solo oculta los botones; quien autoriza es el servidor.
 */
export type AccionAdministrativa =
  | 'gestionar_propietarios'
  | 'gestionar_apartaestudios'
  | 'gestionar_residentes'
  | 'gestionar_bloqueos'
  | 'anular_contratos';

export function puede(usuario: UsuarioActual | null, _accion: AccionAdministrativa): boolean {
  return usuario?.rol === 'administrador';
}
