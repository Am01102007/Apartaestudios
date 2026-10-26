import { clienteHttp } from './cliente';
import { consulta, enviar } from './consulta';
import {
  Apartaestudio,
  ApartaestudioCrear,
  ApartaestudioEditar,
  Contrato,
  Ocupacion,
} from './tipos';

export const listarApartaestudios = (
  filtros: {
    propietario_id?: number;
    ocupacion?: Ocupacion;
    en_mantenimiento?: boolean;
    activo?: boolean;
    texto?: string;
  } = {}
) => clienteHttp<Apartaestudio[]>(`/apartaestudios${consulta(filtros)}`);

export const obtenerApartaestudio = (id: number) =>
  clienteHttp<Apartaestudio>(`/apartaestudios/${id}`);

export const crearApartaestudio = (datos: ApartaestudioCrear) =>
  clienteHttp<Apartaestudio>('/apartaestudios', enviar('POST', datos));

export const actualizarApartaestudio = (id: number, datos: ApartaestudioEditar) =>
  clienteHttp<Apartaestudio>(`/apartaestudios/${id}`, enviar('PATCH', datos));

export const obtenerContratosApartaestudio = (id: number) =>
  clienteHttp<Contrato[]>(`/apartaestudios/${id}/contratos`);

/** Marca (activo=true) o retira (activo=false) el mantenimiento; el motivo es obligatorio. */
export const cambiarMantenimiento = (id: number, activo: boolean, motivo: string) =>
  clienteHttp<Apartaestudio>(
    `/apartaestudios/${id}/mantenimiento`,
    enviar('POST', { activo, motivo })
  );

export const activarApartaestudio = (id: number) =>
  clienteHttp<Apartaestudio>(`/apartaestudios/${id}/activar`, enviar('POST'));

export const desactivarApartaestudio = (id: number) =>
  clienteHttp<Apartaestudio>(`/apartaestudios/${id}/desactivar`, enviar('POST'));
