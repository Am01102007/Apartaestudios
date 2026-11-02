import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  abierto: boolean;
  alCerrar: () => void;
  titulo: string;
  subtitulo?: string;
  children: React.ReactNode;
  tamano?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  abierto,
  alCerrar,
  titulo,
  subtitulo,
  children,
  tamano = 'md',
}) => {
  useEffect(() => {
    const manejarTecla = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && abierto) {
        alCerrar();
      }
    };
    if (abierto) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', manejarTecla);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', manejarTecla);
    };
  }, [abierto, alCerrar]);

  if (!abierto) return null;

  const anchoClases = {
    sm: 'max-w-md',
    md: 'max-w-xl',
    lg: 'max-w-3xl',
    xl: 'max-w-4xl',
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto"
    >
      {/* Telón de fondo */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-xs transition-opacity"
        onClick={alCerrar}
      />

      {/* Contenedor del Modal */}
      <div
        className={`relative w-full ${anchoClases[tamano]} bg-fondo text-tinta border border-linea-fuerte/50 rounded-lg shadow-2xl z-10 my-8 overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div className="px-6 py-5 border-b border-linea flex items-start justify-between bg-panel">
          <div>
            <h2 className="text-xl sm:text-2xl font-titulo font-medium tracking-tight text-tinta">
              {titulo}
            </h2>
            {subtitulo && (
              <p className="text-xs text-tinta-2 mt-1 ">
                {subtitulo}
              </p>
            )}
          </div>
          <button
            onClick={alCerrar}
            className="p-1.5 text-tenue hover:text-tinta hover:bg-black/5 dark:hover:bg-white/5 rounded-lg transition-colors cursor-pointer"
            aria-label="Cerrar modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido */}
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};
