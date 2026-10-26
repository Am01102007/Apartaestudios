import { clienteHttp } from './cliente';
import { consulta, enviar } from './consulta';
import { Propietario, PropietarioCrear, PropietarioDetalle, PropietarioEditar } from './tipos';

export const listarPropietarios = (filtros: { activo?: boolean; texto?: string } = {}) =>
  clienteHttp<Propietario[]>(`/propietarios${consulta(filtros)}`);

export const obtenerPropietario = (id: number) =>
  clienteHttp<PropietarioDetalle>(`/propietarios/${id}`);

export const crearPropietario = (datos: PropietarioCrear) =>
  clienteHttp<Propietario>('/propietarios', enviar('POST', datos));

export const actualizarPropietario = (id: number, datos: PropietarioEditar) =>
  clienteHttp<Propietario>(`/propietarios/${id}`, enviar('PATCH', datos));

export const activarPropietario = (id: number) =>
  clienteHttp<Propietario>(`/propietarios/${id}/activar`, enviar('POST'));

export const desactivarPropietario = (id: number) =>
  clienteHttp<Propietario>(`/propietarios/${id}/desactivar`, enviar('POST'));
