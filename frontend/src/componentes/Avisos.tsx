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
            'bg-peligro-bg text-peligro border-peligro/40',
          exito:
            'bg-exito-bg text-exito border-exito/40',
          advertencia:
            'bg-aviso-bg text-aviso border-aviso/40',
          info:
            'bg-sutil text-tinta border-linea-fuerte',
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
            className={`pointer-events-auto flex items-start gap-3 p-4 rounded-lg border shadow-lg transition-all animate-in fade-in slide-in-from-top-2 ${estilos}`}
          >
            <div className="mt-0.5">{icono}</div>
            <div className="flex-1 text-sm  leading-snug">
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
