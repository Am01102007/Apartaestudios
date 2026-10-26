import React from 'react';
import { AlertCircle } from 'lucide-react';

interface CampoProps {
  label: string;
  obligatorio?: boolean;
  error?: string;
  ayuda?: string;
  children: React.ReactNode;
  id?: string;
}

export const Campo: React.FC<CampoProps> = ({
  label,
  obligatorio = false,
  error,
  ayuda,
  children,
  id,
}) => {
  return (
    <div className="flex flex-col gap-1.5 w-full">
      <div className="flex items-center justify-between">
        <label
          htmlFor={id}
          className="text-[11px] font-medium tracking-widest uppercase text-[#5A5D62] dark:text-[#A0A3A8]"
        >
          {label} {obligatorio && <span className="text-[#7A1F2B] font-bold">*</span>}
        </label>
        {ayuda && !error && (
          <span className="text-[11px] text-[#8A8D91] italic">{ayuda}</span>
        )}
      </div>

      <div className="relative">{children}</div>

      {error && (
        <p className="flex items-center gap-1.5 text-xs text-[#7A1F2B] dark:text-[#E89AA3] mt-0.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </p>
      )}
    </div>
  );
};

export const EntradaTexto = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { tieneError?: boolean }
>(({ tieneError, className = '', ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={`w-full px-3.5 py-2 text-sm bg-white dark:bg-[#141416] text-[#0B0B0C] dark:text-[#FAFAF9] border rounded-[4px] transition-colors outline-none focus:ring-1 ${
        tieneError
          ? 'border-[#7A1F2B] focus:border-[#7A1F2B] focus:ring-[#7A1F2B]'
          : 'border-[#C0C0C0] dark:border-[#3A3A3E] focus:border-[#1A1A1D] dark:focus:border-[#FAFAF9] focus:ring-[#1A1A1D] dark:focus:ring-[#FAFAF9]'
      } disabled:bg-[#F4F5F6] dark:disabled:bg-[#1E1E22] disabled:cursor-not-allowed ${className}`}
      {...props}
    />
  );
});

EntradaTexto.displayName = 'EntradaTexto';

export const EntradaSeleccion = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement> & { tieneError?: boolean }
>(({ tieneError, className = '', children, ...props }, ref) => {
  return (
    <select
      ref={ref}
      className={`w-full px-3 py-2 text-sm bg-white dark:bg-[#141416] text-[#0B0B0C] dark:text-[#FAFAF9] border rounded-[4px] transition-colors outline-none focus:ring-1 ${
        tieneError
          ? 'border-[#7A1F2B] focus:border-[#7A1F2B] focus:ring-[#7A1F2B]'
          : 'border-[#C0C0C0] dark:border-[#3A3A3E] focus:border-[#1A1A1D] dark:focus:border-[#FAFAF9] focus:ring-[#1A1A1D] dark:focus:ring-[#FAFAF9]'
      } disabled:bg-[#F4F5F6] dark:disabled:bg-[#1E1E22] disabled:cursor-not-allowed ${className}`}
      {...props}
    >
      {children}
    </select>
  );
});

EntradaSeleccion.displayName = 'EntradaSeleccion';

export const EntradaAreaTexto = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { tieneError?: boolean }
>(({ tieneError, className = '', ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      rows={3}
      className={`w-full px-3.5 py-2 text-sm bg-white dark:bg-[#141416] text-[#0B0B0C] dark:text-[#FAFAF9] border rounded-[4px] transition-colors outline-none focus:ring-1 resize-y ${
        tieneError
          ? 'border-[#7A1F2B] focus:border-[#7A1F2B] focus:ring-[#7A1F2B]'
          : 'border-[#C0C0C0] dark:border-[#3A3A3E] focus:border-[#1A1A1D] dark:focus:border-[#FAFAF9] focus:ring-[#1A1A1D] dark:focus:ring-[#FAFAF9]'
      } disabled:bg-[#F4F5F6] dark:disabled:bg-[#1E1E22] disabled:cursor-not-allowed ${className}`}
      {...props}
    />
  );
});

EntradaAreaTexto.displayName = 'EntradaAreaTexto';
