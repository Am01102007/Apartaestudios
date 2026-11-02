import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexto/AuthContext';
import {
  LayoutDashboard,
  Building2,
  FileText,
  Users,
  Briefcase,
  ShieldAlert,
  UserCog,
  History,
  LogOut,
  Menu,
  X,
  Moon,
  Sun,
  KeyRound,
  Shield,
} from 'lucide-react';
import { ContenedorAvisos } from './Avisos';
import { FondoParticulas } from './FondoParticulas';

export const DisenoPrincipal: React.FC = () => {
  const { usuario, esAdmin, cerrarSesion, temaOscuro, alternarTema } = useAuth();
  const [menuMovilAbierto, setMenuMovilAbierto] = useState(false);
  const navigate = useNavigate();

  const handleCerrarSesion = async () => {
    // Primero se sale de la pantalla actual (sin dejarla en el historial) y luego se cierra la sesión.
    navigate('/ingresar', { replace: true });
    await cerrarSesion();
  };

  const enlacesNavegacion = [
    { to: '/', label: 'Inicio', icon: LayoutDashboard },
    { to: '/apartaestudios', label: 'Apartaestudios', icon: Building2 },
    { to: '/contratos', label: 'Contratos', icon: FileText },
    { to: '/residentes', label: 'Residentes', icon: Users },
    { to: '/propietarios', label: 'Propietarios', icon: Briefcase },
    { to: '/bloqueos', label: 'Bloqueos', icon: ShieldAlert },
    ...(esAdmin
      ? [
          { to: '/usuarios', label: 'Usuarios', icon: UserCog },
          { to: '/auditoria', label: 'Auditoría', icon: History },
        ]
      : []),
  ];

  const Marca = ({ compacta = false }: { compacta?: boolean }) => (
    <div className="flex items-center gap-2.5">
      <div
        className={`${compacta ? 'w-7 h-7' : 'w-9 h-9'} rounded-xl bg-tinta text-sobre-tinta flex items-center justify-center`}
      >
        <Building2 className={compacta ? 'w-4 h-4' : 'w-5 h-5'} />
      </div>
      <div className="leading-tight">
        <span className="font-titulo text-lg font-semibold tracking-tight text-tinta">
          Aura<span className="text-acento-fuerte">.</span>
        </span>
        {!compacta && (
          <p className="text-[10px] tracking-[0.2em] text-tenue uppercase">Apartaestudios</p>
        )}
      </div>
    </div>
  );

  const BotonTema = ({ className = '' }: { className?: string }) => (
    <button
      onClick={alternarTema}
      title={temaOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      aria-label={temaOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      className={`p-2 rounded-lg text-tenue hover:text-tinta hover:bg-sutil transition-colors cursor-pointer ${className}`}
    >
      {temaOscuro ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </button>
  );

  return (
    <div className="relative min-h-screen flex bg-fondo text-tinta">
      <FondoParticulas />
      <ContenedorAvisos />

      {/* Fondo oscuro del menú en el celular */}
      {menuMovilAbierto && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs md:hidden"
          onClick={() => setMenuMovilAbierto(false)}
        />
      )}

      {/* Barra lateral */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-50 h-screen w-64 bg-panel border-r border-linea flex flex-col justify-between transition-transform duration-200 ease-in-out md:translate-x-0 ${
          menuMovilAbierto ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div>
          <div className="px-5 py-5 flex items-center justify-between">
            <Marca />
            <button
              onClick={() => setMenuMovilAbierto(false)}
              className="p-1 md:hidden text-tenue hover:text-tinta"
              aria-label="Cerrar menú"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="h-px bg-linea mx-5" />

          <nav className="p-3 space-y-1">
            <div className="px-3 pt-3 pb-2 text-[10px] tracking-[0.2em] uppercase text-tenue font-semibold">
              Módulos
            </div>
            {enlacesNavegacion.map((item) => {
              const Icono = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={() => setMenuMovilAbierto(false)}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-sutil text-tinta shadow-[inset_2px_0_0_var(--c-acento)]'
                        : 'text-tinta-2 hover:text-tinta hover:bg-sutil'
                    }`
                  }
                >
                  <Icono className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Usuario, tema y salida */}
        <div className="p-3 border-t border-linea">
          {usuario && (
            <div className="mb-2 px-2 py-2 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2.5 overflow-hidden">
                <div className="w-8 h-8 shrink-0 rounded-full bg-sutil text-tinta-2 border border-linea flex items-center justify-center text-xs font-semibold uppercase">
                  {usuario.nombre.slice(0, 1)}
                </div>
                <div className="overflow-hidden">
                  <p className="text-sm font-medium text-tinta truncate">{usuario.nombre}</p>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Shield className="w-3 h-3 text-tenue" />
                    <span className="text-[10px] tracking-wider uppercase text-tenue">{usuario.rol}</span>
                  </div>
                </div>
              </div>
              <BotonTema />
            </div>
          )}

          <div className="space-y-0.5">
            <NavLink
              to="/cambiar-contrasena"
              onClick={() => setMenuMovilAbierto(false)}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 text-sm rounded-lg transition-colors ${
                  isActive ? 'text-tinta bg-sutil' : 'text-tinta-2 hover:text-tinta hover:bg-sutil'
                }`
              }
            >
              <KeyRound className="w-4 h-4" />
              <span>Cambiar Contraseña</span>
            </NavLink>

            <button
              onClick={handleCerrarSesion}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-sm rounded-lg text-tinta-2 hover:text-peligro hover:bg-peligro-bg transition-colors cursor-pointer text-left"
            >
              <LogOut className="w-4 h-4" />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Contenido principal */}
      <div className="relative z-10 flex-1 flex flex-col min-w-0">
        {/* Barra superior en el celular */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-panel border-b border-linea sticky top-0 z-30">
          <button
            onClick={() => setMenuMovilAbierto(true)}
            className="p-1 text-tinta-2 hover:text-tinta"
            aria-label="Abrir menú de navegación"
          >
            <Menu className="w-6 h-6" />
          </button>
          <Marca compacta />
          <BotonTema />
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
