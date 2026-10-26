/**
 * Tipos de la API, derivados de esquema.d.ts (generado desde openapi.json del backend).
 * Para regenerarlo:  npx openapi-typescript@7 openapi.json -o src/api/esquema.d.ts
 */
import type { components } from './esquema';

type S = components['schemas'];

export type TipoDocumento = S['TipoDocumento'];
export type RolUsuario = S['Rol'];
export type Ocupacion = S['Ocupacion'];
export type EstadoContrato = S['EstadoContrato'];
export type EstadoBloqueo = S['EstadoBloqueo'];

export const TIPOS_DOCUMENTO: TipoDocumento[] = ['CC', 'CE', 'NIT', 'PA', 'PPT'];
export const NOMBRES_TIPO_DOCUMENTO: Record<TipoDocumento, string> = {
  CC: 'Cédula de ciudadanía',
  CE: 'Cédula de extranjería',
  NIT: 'NIT',
  PA: 'Pasaporte',
  PPT: 'Permiso por protección temporal',
};
export const ESTADOS_CONTRATO: EstadoContrato[] = [
  'por_iniciar',
  'vigente',
  'vencido',
  'en_terminacion',
  'terminado',
  'renovado',
  'anulado',
];
export const NOMBRES_ESTADO_CONTRATO: Record<EstadoContrato, string> = {
  por_iniciar: 'Por iniciar',
  vigente: 'Vigente',
  vencido: 'Vencido',
  en_terminacion: 'En terminación',
  terminado: 'Terminado',
  renovado: 'Renovado',
  anulado: 'Anulado',
};

export interface ErrorItem {
  campo: string;
  mensaje: string;
  tipo?: string;
}

export interface ErrorDetalle {
  codigo: string;
  mensaje: string;
  detalles?: ErrorItem[];
}

export type UsuarioActual = S['UsuarioActual'];
export type Usuario = S['UsuarioSalida'];
export type UsuarioCrear = S['UsuarioCrear'];
export type UsuarioEditar = S['UsuarioEditar'];

export type Propietario = S['PropietarioSalida'];
export type PropietarioDetalle = S['PropietarioDetalle'];
export type PropietarioCrear = S['PropietarioCrear'];
export type PropietarioEditar = S['PropietarioEditar'];

export type Apartaestudio = S['ApartaestudioSalida'];
export type ApartaestudioResumen = S['ApartaestudioResumen'];
export type ApartaestudioCrear = S['ApartaestudioCrear'];
export type ApartaestudioEditar = S['ApartaestudioEditar'];

export type Residente = S['ResidenteSalida'];
export type ResidenteDetalle = S['ResidenteDetalle'];
export type ResidenteCrear = S['ResidenteCrear'];
export type ResidenteEditar = S['ResidenteEditar'];

export type Bloqueo = S['BloqueoSalida'];
export type BloqueoCrear = S['BloqueoCrear'];
export type VerificarBloqueoRespuesta = S['Verificacion'];

export type Contrato = S['ContratoSalida'];
export type ContratoDetalle = S['ContratoDetalle'];
export type ContratoCrear = S['ContratoCrear'];
export type ContratoEditar = S['ContratoEditar'];
export type ProrrogaCrear = S['ProrrogaCrear'];
export type RenovacionCrear = S['RenovacionCrear'];
export type TerminacionCrear = S['TerminacionCrear'];
export type CambioContrato = S['Cambio'];

export type RegistroAuditoria = S['RegistroAuditoriaSalida'];
export type PaginaAuditoria = S['PaginaAuditoria'];

/** Estado que se muestra en pantalla: el mantenimiento prevalece sobre la ocupación. */
export type EstadoApartaestudio = Ocupacion | 'mantenimiento';
export const estadoApartaestudio = (a: {
  ocupacion: Ocupacion;
  en_mantenimiento: boolean;
}): EstadoApartaestudio => (a.en_mantenimiento ? 'mantenimiento' : a.ocupacion);
