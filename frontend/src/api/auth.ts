import { clienteHttp } from './cliente';
import { enviar } from './consulta';
import { UsuarioActual } from './tipos';

export const login = (nombre_usuario: string, contrasena: string) =>
  clienteHttp<UsuarioActual>('/auth/login', enviar('POST', { nombre_usuario, contrasena }));

export const obtenerYo = () => clienteHttp<UsuarioActual>('/auth/yo');

export const logout = () => clienteHttp<void>('/auth/logout', enviar('POST'));

export const cambiarContrasena = (contrasena_actual: string, contrasena_nueva: string) =>
  clienteHttp<void>(
    '/auth/cambiar-contrasena',
    enviar('POST', { contrasena_actual, contrasena_nueva })
  );
