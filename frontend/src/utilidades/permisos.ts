import { UsuarioActual } from '../api/tipos';

/**
 * Acciones que la pantalla muestra u oculta según el rol. Sigue la tabla de roles de la propuesta
 * (sección 4), con los ajustes decididos el 2 de noviembre: el empleado registra residentes, pero no
 * edita ni desactiva nada (tampoco contratos). La pantalla solo oculta los botones; quien autoriza
 * es el servidor.
 */
export type AccionAdministrativa =
  | 'crear_residentes'
  | 'gestionar_propietarios'
  | 'gestionar_apartaestudios'
  | 'gestionar_residentes'
  | 'gestionar_bloqueos'
  | 'editar_contratos'
  | 'anular_contratos';

export function puede(usuario: UsuarioActual | null, accion: AccionAdministrativa): boolean {
  if (!usuario) return false;
  if (accion === 'crear_residentes') return true;
  return usuario.rol === 'administrador';
}
