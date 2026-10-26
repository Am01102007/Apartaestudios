import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexto/AuthContext';
import { Loader2, ShieldAlert } from 'lucide-react';
import { Boton } from './Boton';

interface RutaProtegidaProps {
  children: React.ReactNode;
  requiereAdmin?: boolean;
}

export const RutaProtegida: React.FC<RutaProtegidaProps> = ({
  children,
  requiereAdmin = false,
}) => {
  const { usuario, cargando, debeCambiarContrasena, esAdmin } = useAuth();
  const location = useLocation();

  if (cargando) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#FAFAF9] dark:bg-[#0B0B0C] text-[#0B0B0C] dark:text-[#FAFAF9]">
        <div className="w-8 h-8 border border-[#C0C0C0] flex items-center justify-center rotate-45 mb-4 animate-pulse">
          <div className="w-3.5 h-3.5 bg-[#C0C0C0] -rotate-45" />
        </div>
        <Loader2 className="w-5 h-5 animate-spin text-[#8A8D91] mb-2" />
        <p className="text-xs tracking-widest uppercase text-[#5A5D62] dark:text-[#A0A3A8]">
          Verificando sesión segura...
        </p>
      </div>
    );
  }

  // Si no hay sesión, ir a /ingresar
  if (!usuario) {
    return <Navigate to="/ingresar" state={{ desde: location }} replace />;
  }

  // Si tiene que cambiar contraseña y no está en la pantalla de cambiar contraseña
  if (debeCambiarContrasena && location.pathname !== '/cambiar-contrasena') {
    return <Navigate to="/cambiar-contrasena" replace />;
  }

  // Si requiere administrador y no lo es
  if (requiereAdmin && !esAdmin) {
    return (
      <div className="py-16 text-center max-w-lg mx-auto">
        <div className="w-14 h-14 rounded-full bg-[#FCF4F5] dark:bg-[#251013] text-[#7A1F2B] dark:text-[#E89AA3] flex items-center justify-center mx-auto mb-4 border border-[#7A1F2B]/30">
          <ShieldAlert className="w-7 h-7" />
        </div>
        <h2 className="text-2xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9]">
          Acceso Restringido
        </h2>
        <p className="text-sm text-[#5A5D62] dark:text-[#A0A3A8] mt-2 font-sans-clean">
          No tienes permiso para esta acción. Este módulo está reservado exclusivamente para administradores.
        </p>
        <div className="mt-6">
          <Boton onClick={() => window.history.back()} variante="secundario">
            Volver a la página anterior
          </Boton>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
