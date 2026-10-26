import { clienteHttp } from './cliente';
import { consulta, enviar } from './consulta';
import {
  CambioContrato,
  Contrato,
  ContratoCrear,
  ContratoDetalle,
  ContratoEditar,
  EstadoContrato,
  RenovacionCrear,
  TerminacionCrear,
} from './tipos';

export const listarContratos = (
  filtros: {
    estado?: EstadoContrato;
    propietario_id?: number;
    apartaestudio_id?: number;
    residente_id?: number;
  } = {}
) => clienteHttp<Contrato[]>(`/contratos${consulta(filtros)}`);

export const obtenerContrato = (id: number) =>
  clienteHttp<ContratoDetalle>(`/contratos/${id}`);

export const crearContrato = (datos: ContratoCrear) =>
  clienteHttp<ContratoDetalle>('/contratos', enviar('POST', datos));

/** Solo para contratos que aún no tienen cobros. */
export const actualizarContrato = (id: number, datos: ContratoEditar) =>
  clienteHttp<ContratoDetalle>(`/contratos/${id}`, enviar('PATCH', datos));

export const obtenerHistorialContrato = (id: number) =>
  clienteHttp<CambioContrato[]>(`/contratos/${id}/historial`);

export const prorrogarContrato = (id: number, fecha_terminacion: string) =>
  clienteHttp<ContratoDetalle>(`/contratos/${id}/prorrogar`, enviar('POST', { fecha_terminacion }));

export const renovarContrato = (id: number, datos: RenovacionCrear) =>
  clienteHttp<ContratoDetalle>(`/contratos/${id}/renovar`, enviar('POST', datos));

export const terminarContrato = (id: number, datos: TerminacionCrear) =>
  clienteHttp<ContratoDetalle>(`/contratos/${id}/terminar`, enviar('POST', datos));

export const anularContrato = (id: number, motivo: string) =>
  clienteHttp<ContratoDetalle>(`/contratos/${id}/anular`, enviar('POST', { motivo }));
