import { clienteHttp } from './cliente';
import { consulta } from './consulta';
import { PaginaAuditoria } from './tipos';

export const listarAuditoria = (
  filtros: {
    usuario_id?: number;
    accion?: string;
    entidad?: string;
    entidad_id?: string;
    desde?: string;
    hasta?: string;
    limite?: number;
    desplazamiento?: number;
  } = {}
) => clienteHttp<PaginaAuditoria>(`/auditoria${consulta(filtros)}`);
