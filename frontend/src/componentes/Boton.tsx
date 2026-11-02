import React from 'react';
import { Loader2 } from 'lucide-react';

interface BotonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: 'primario' | 'secundario' | 'peligro' | 'fantasma' | 'plata';
  tamano?: 'sm' | 'md' | 'lg';
  cargando?: boolean;
  icono?: React.ReactNode;
}

export const Boton: React.FC<BotonProps> = ({
  children,
  variante = 'primario',
  tamano = 'md',
  cargando = false,
  icono,
  disabled,
  className = '',
  ...props
}) => {
  const tamanoClases = {
    sm: 'px-3 py-1.5 text-xs tracking-wider uppercase',
    md: 'px-4 py-2 text-sm tracking-wide',
    lg: 'px-6 py-2.5 text-base tracking-wide',
  };

  const varianteClases = {
    primario:
      'bg-tinta text-sobre-tinta border border-transparent shadow-sm hover:opacity-90 active:translate-y-px',
    plata:
      'bg-tinta text-sobre-tinta border border-transparent shadow-sm hover:opacity-90 active:translate-y-px',
    secundario:
      'bg-panel text-tinta border border-linea-fuerte hover:border-tenue hover:bg-sutil',
    peligro:
      'bg-peligro text-sobre-tinta border border-transparent hover:brightness-110 shadow-sm',
    fantasma:
      'bg-transparent hover:bg-black/5 dark:hover:bg-white/5 text-current border border-transparent',
  };

  return (
    <button
      disabled={disabled || cargando}
      className={`inline-flex items-center justify-center font-medium transition-all duration-150 rounded-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-acento focus-visible:ring-offset-2 focus-visible:ring-offset-fondo ${tamanoClases[tamano]} ${varianteClases[variante]} ${className}`}
      {...props}
    >
      {cargando ? (
        <Loader2 className="w-4 h-4 mr-2 animate-spin text-current" />
      ) : icono ? (
        <span className="mr-2 inline-flex items-center">{icono}</span>
      ) : null}
      <span>{children}</span>
    </button>
  );
};
