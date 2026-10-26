import { clienteHttp } from './cliente';
import { consulta, enviar } from './consulta';
import { RolUsuario, Usuario, UsuarioCrear, UsuarioEditar } from './tipos';

export const listarUsuarios = (filtros: { rol?: RolUsuario; activo?: boolean } = {}) =>
  clienteHttp<Usuario[]>(`/usuarios${consulta(filtros)}`);

export const crearUsuario = (datos: UsuarioCrear) =>
  clienteHttp<Usuario>('/usuarios', enviar('POST', datos));

export const actualizarUsuario = (id: number, datos: UsuarioEditar) =>
  clienteHttp<Usuario>(`/usuarios/${id}`, enviar('PATCH', datos));

export const activarUsuario = (id: number) =>
  clienteHttp<Usuario>(`/usuarios/${id}/activar`, enviar('POST'));

export const desactivarUsuario = (id: number) =>
  clienteHttp<Usuario>(`/usuarios/${id}/desactivar`, enviar('POST'));

export const restablecerContrasenaUsuario = (id: number, contrasena_temporal: string) =>
  clienteHttp<Usuario>(
    `/usuarios/${id}/restablecer-contrasena`,
    enviar('POST', { contrasena_temporal })
  );
