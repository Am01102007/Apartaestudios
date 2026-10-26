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
    tamano === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs tracking-wider';

  // 1. Estado apartaestudio
  if (tipo === 'apartaestudio') {
    const estado = valor as EstadoApartaestudio;
    if (estado === 'libre') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#F4F5F6] text-[#1A1A1D] border border-[#C0C0C0] dark:bg-[#1A1A1D] dark:text-[#FAFAF9] dark:border-[#3A3A3E] ${tamanoClase}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-[#5A5D62] dark:text-[#C0C0C0]" />
          Libre
        </span>
      );
    }
    if (estado === 'ocupado') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#0B0B0C] text-[#FAFAF9] border border-[#2A2A2E] dark:bg-[#FAFAF9] dark:text-[#0B0B0C] dark:border-[#E3E4E6] ${tamanoClase}`}
        >
          <Lock className="w-3.5 h-3.5" />
          Ocupado
        </span>
      );
    }
    if (estado === 'mantenimiento') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#EAEBED] text-[#4A4D52] border border-[#8A8D91] dark:bg-[#222326] dark:text-[#C0C0C0] dark:border-[#4A4D52] ${tamanoClase}`}
        >
          <Wrench className="w-3.5 h-3.5 text-[#8A8D91]" />
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
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#F2F7F6] text-[#2F4F4A] border border-[#2F4F4A]/30 dark:bg-[#122926] dark:text-[#84C9BE] dark:border-[#2F4F4A] ${tamanoClase}`}
        >
          <FileCheck2 className="w-3.5 h-3.5 text-[#2F4F4A] dark:text-[#84C9BE]" />
          Vigente
        </span>
      );
    }
    if (estado === 'vencido') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#FCF4F5] text-[#7A1F2B] border border-[#7A1F2B]/30 dark:bg-[#2E1015] dark:text-[#E89AA3] dark:border-[#7A1F2B] ${tamanoClase}`}
        >
          <Clock className="w-3.5 h-3.5 text-[#7A1F2B] dark:text-[#E89AA3]" />
          Vencido
        </span>
      );
    }
    if (estado === 'por_iniciar' || estado === 'en_terminacion') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#F4F5F6] text-[#1A1A1D] border border-[#8A8D91] dark:bg-[#1A1A1D] dark:text-[#E3E4E6] dark:border-[#4A4D52] ${tamanoClase}`}
        >
          <Clock className="w-3.5 h-3.5 text-[#8A8D91]" />
          {NOMBRES_ESTADO_CONTRATO[estado]}
        </span>
      );
    }
    if (estado === 'terminado' || estado === 'renovado') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#EAEBED] text-[#5A5D62] border border-[#C0C0C0] dark:bg-[#1A1A1D] dark:text-[#A0A3A8] dark:border-[#3A3A3E] ${tamanoClase}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-[#8A8D91]" />
          {NOMBRES_ESTADO_CONTRATO[estado]}
        </span>
      );
    }
    if (estado === 'anulado') {
      return (
        <span
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#2A2A2E] text-[#E3E4E6] border border-[#5A5D62] dark:bg-[#1A1A1D] dark:text-[#8A8D91] dark:border-[#3A3A3E] ${tamanoClase}`}
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
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#FCF4F5] text-[#7A1F2B] border border-[#7A1F2B]/40 dark:bg-[#2E1015] dark:text-[#E89AA3] dark:border-[#7A1F2B] ${tamanoClase}`}
        >
          <AlertCircle className="w-3.5 h-3.5 text-[#7A1F2B] dark:text-[#E89AA3]" />
          Bloqueado
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#F2F7F6] text-[#2F4F4A] border border-[#2F4F4A]/30 dark:bg-[#122926] dark:text-[#84C9BE] ${tamanoClase}`}
      >
        <ShieldCheck className="w-3.5 h-3.5 text-[#2F4F4A] dark:text-[#84C9BE]" />
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
          className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#F2F7F6] text-[#2F4F4A] border border-[#2F4F4A]/30 dark:bg-[#122926] dark:text-[#84C9BE] ${tamanoClase}`}
        >
          <UserCheck className="w-3.5 h-3.5 text-[#2F4F4A] dark:text-[#84C9BE]" />
          Activo
        </span>
      );
    }
    return (
      <span
        className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#EAEBED] text-[#5A5D62] border border-[#C0C0C0] dark:bg-[#1A1A1D] dark:text-[#8A8D91] ${tamanoClase}`}
      >
        <UserX className="w-3.5 h-3.5 text-[#8A8D91]" />
        Inactivo
      </span>
    );
  }

  // 5. Rol
  if (tipo === 'rol') {
    const rol = String(valor);
    return (
      <span
        className={`inline-flex items-center gap-1.5 uppercase font-medium rounded-[4px] bg-[#1A1A1D] text-[#FAFAF9] border border-[#8A8D91] dark:bg-[#2A2A2E] dark:text-[#FAFAF9] ${tamanoClase}`}
      >
        {rol === 'administrador' ? 'Administrador' : 'Empleado'}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center font-medium rounded-[4px] bg-gray-100 text-gray-800 ${tamanoClase}`}>
      {String(valor)}
    </span>
  );
};
