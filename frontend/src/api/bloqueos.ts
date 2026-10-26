import { clienteHttp } from './cliente';
import { consulta, enviar } from './consulta';
import {
  Bloqueo,
  BloqueoCrear,
  EstadoBloqueo,
  TipoDocumento,
  VerificarBloqueoRespuesta,
} from './tipos';

export const listarBloqueos = (filtros: { estado?: EstadoBloqueo; texto?: string } = {}) =>
  clienteHttp<Bloqueo[]>(`/bloqueos${consulta(filtros)}`);

export const crearBloqueo = (datos: BloqueoCrear) =>
  clienteHttp<Bloqueo>('/bloqueos', enviar('POST', datos));

export const levantarBloqueo = (id: number, motivo: string) =>
  clienteHttp<Bloqueo>(`/bloqueos/${id}/levantar`, enviar('POST', { motivo }));

export const verificarBloqueo = (tipo_documento: TipoDocumento, numero_documento: string) =>
  clienteHttp<VerificarBloqueoRespuesta>(
    `/bloqueos/verificar${consulta({ tipo_documento, numero_documento })}`
  );
