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
      'bg-[#111113] hover:bg-[#1f1f23] text-[#FAFAF9] border border-[#3A3A3E] hover:border-[#C0C0C0] shadow-sm',
    plata:
      'bg-gradient-to-b from-[#2A2A2E] to-[#141416] text-[#FAFAF9] border border-[#8A8D91] hover:border-[#E3E4E6] shadow-sm',
    secundario:
      'bg-[#FAFAF9] hover:bg-[#EAEBED] text-[#1A1A1D] border border-[#C0C0C0] dark:bg-[#1A1A1D] dark:text-[#FAFAF9] dark:border-[#3A3A3E] dark:hover:bg-[#252529]',
    peligro:
      'bg-[#7A1F2B] hover:bg-[#922534] text-[#FAFAF9] border border-[#5A141E] shadow-sm',
    fantasma:
      'bg-transparent hover:bg-black/5 dark:hover:bg-white/5 text-current border border-transparent',
  };

  return (
    <button
      disabled={disabled || cargando}
      className={`inline-flex items-center justify-center font-medium transition-all duration-150 rounded-[4px] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none focus:outline-none focus:ring-2 focus:ring-[#C0C0C0] focus:ring-offset-1 ${tamanoClases[tamano]} ${varianteClases[variante]} ${className}`}
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
