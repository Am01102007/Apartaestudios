import React from 'react';
import {
  CheckCircle2,
  Lock,
  Wrench,
  AlertCircle,
  FileCheck2,
  Clock,
  Ban,
  ShieldCheck,
  UserCheck,
  UserX,
} from 'lucide-react';
import { EstadoApartaestudio, EstadoContrato, NOMBRES_ESTADO_CONTRATO } from '../api/tipos';

interface InsigniaEstadoProps {
  tipo:
    | 'apartaestudio'
    | 'contrato'
    | 'bloqueo'
    | 'activo'
    | 'rol';
  valor: string | boolean;
  tamano?: 'sm' | 'md';
}

export const InsigniaEstado: React.FC<InsigniaEstadoProps> = ({
  tipo,
  valor,
  tamano = 'md',
}) => {
  const tamanoClase =
    tamano === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-[11px] tracking-wider';

  // 1. Estado apartaestudio
  if (tipo === 'apartaestudio') {
    const estado = valor as EstadoApartaestudio;
    if (estado === 'libre') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-sutil text-tinta border border-linea-fuerte ${tamanoClase}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Libre
        </span>
      );
    }
    if (estado === 'ocupado') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-tinta text-sobre-tinta border border-transparent ${tamanoClase}`}
        >
          <Lock className="w-3.5 h-3.5" />
          Ocupado
        </span>
      );
    }
    if (estado === 'mantenimiento') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-aviso-bg text-aviso border border-aviso/40 ${tamanoClase}`}
        >
          <Wrench className="w-3.5 h-3.5" />
          Mantenimiento
        </span>
      );
    }
  }

  // 2. Estado contrato
  if (tipo === 'contrato') {
    const estado = valor as EstadoContrato;
    if (estado === 'vigente') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-exito-bg text-exito border border-exito/30 ${tamanoClase}`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          Vigente
        </span>
      );
    }
    if (estado === 'vencido') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-peligro-bg text-peligro border border-peligro/40 ${tamanoClase}`}
        >
          <Clock className="w-3.5 h-3.5" />
          Vencido
        </span>
      );
    }
    if (estado === 'por_iniciar' || estado === 'en_terminacion') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-sutil text-tinta border border-linea-fuerte ${tamanoClase}`}
        >
          <Clock className="w-3.5 h-3.5" />
          {NOMBRES_ESTADO_CONTRATO[estado]}
        </span>
      );
    }
    if (estado === 'terminado' || estado === 'renovado') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-sutil text-tenue border border-linea ${tamanoClase}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          {NOMBRES_ESTADO_CONTRATO[estado]}
        </span>
      );
    }
    if (estado === 'anulado') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-sutil text-tenue border border-linea ${tamanoClase}`}
        >
          <Ban className="w-3.5 h-3.5" />
          Anulado
        </span>
      );
    }
  }

  // 3. Bloqueo
  if (tipo === 'bloqueo') {
    const estaBloqueado = Boolean(valor);
    if (estaBloqueado) {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-peligro-bg text-peligro border border-peligro/40 ${tamanoClase}`}
        >
          <AlertCircle className="w-3.5 h-3.5" />
          Bloqueado
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-exito-bg text-exito border border-exito/30 ${tamanoClase}`}
      >
        <ShieldCheck className="w-3.5 h-3.5" />
        Habilitado
      </span>
    );
  }

  // 4. Activo / Inactivo
  if (tipo === 'activo') {
    const activo = Boolean(valor);
    if (activo) {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-exito-bg text-exito border border-exito/30 ${tamanoClase}`}
        >
          <UserCheck className="w-3.5 h-3.5" />
          Activo
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-sutil text-tenue border border-linea ${tamanoClase}`}
      >
        <UserX className="w-3.5 h-3.5" />
        Inactivo
      </span>
    );
  }

  // 5. Rol
  if (tipo === 'rol') {
    const rol = String(valor);
    return (
      <span
        className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-full bg-tinta text-sobre-tinta border border-transparent ${tamanoClase}`}
      >
        {rol === 'administrador' ? 'Administrador' : 'Empleado'}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center font-medium rounded-lg bg-sutil text-tinta ${tamanoClase}`}>
      {String(valor)}
    </span>
  );
};
