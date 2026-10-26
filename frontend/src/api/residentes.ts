import { clienteHttp } from './cliente';
import { consulta, enviar } from './consulta';
import { Contrato, Residente, ResidenteCrear, ResidenteDetalle, ResidenteEditar } from './tipos';

export const listarResidentes = (filtros: { texto?: string } = {}) =>
  clienteHttp<Residente[]>(`/residentes${consulta(filtros)}`);

export const obtenerResidente = (id: number) =>
  clienteHttp<ResidenteDetalle>(`/residentes/${id}`);

export const crearResidente = (datos: ResidenteCrear) =>
  clienteHttp<Residente>('/residentes', enviar('POST', datos));

export const actualizarResidente = (id: number, datos: ResidenteEditar) =>
  clienteHttp<Residente>(`/residentes/${id}`, enviar('PATCH', datos));

export const obtenerContratosResidente = (id: number) =>
  clienteHttp<Contrato[]>(`/residentes/${id}/contratos`);
