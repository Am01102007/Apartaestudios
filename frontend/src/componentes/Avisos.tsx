import React from 'react';
import { useAuth } from '../contexto/AuthContext';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

export const ContenedorAvisos: React.FC = () => {
  const { notificaciones, eliminarNotificacion } = useAuth();

  if (notificaciones.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none px-4 sm:px-0">
      {notificaciones.map((n) => {
        const estilos = {
          error:
            'bg-[#FCF4F5] dark:bg-[#251013] text-[#7A1F2B] dark:text-[#EFA3AC] border-[#7A1F2B]/40',
          exito:
            'bg-[#F2F7F6] dark:bg-[#0E201D] text-[#2F4F4A] dark:text-[#8CD5C8] border-[#2F4F4A]/40',
          advertencia:
            'bg-[#FAF6EE] dark:bg-[#241F14] text-[#805B10] dark:text-[#E8C576] border-[#805B10]/40',
          info:
            'bg-[#F4F5F6] dark:bg-[#1A1A1D] text-[#1A1A1D] dark:text-[#FAFAF9] border-[#C0C0C0]',
        }[n.tipo];

        const icono = {
          error: <AlertCircle className="w-5 h-5 shrink-0" />,
          exito: <CheckCircle2 className="w-5 h-5 shrink-0" />,
          advertencia: <AlertTriangle className="w-5 h-5 shrink-0" />,
          info: <Info className="w-5 h-5 shrink-0" />,
        }[n.tipo];

        return (
          <div
            key={n.id}
            role="alert"
            className={`pointer-events-auto flex items-start gap-3 p-4 rounded-[4px] border shadow-lg transition-all animate-in fade-in slide-in-from-top-2 ${estilos}`}
          >
            <div className="mt-0.5">{icono}</div>
            <div className="flex-1 text-sm font-sans-clean leading-snug">
              <p className="font-medium">{n.mensaje}</p>
            </div>
            <button
              onClick={() => eliminarNotificacion(n.id)}
              className="p-1 opacity-70 hover:opacity-100 transition-opacity cursor-pointer"
              aria-label="Cerrar notificación"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
