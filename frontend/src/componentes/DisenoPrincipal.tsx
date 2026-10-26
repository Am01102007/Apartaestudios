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

export const DisenoPrincipal: React.FC = () => {
  const { usuario, esAdmin, cerrarSesion, temaOscuro, alternarTema } = useAuth();
  const [menuMovilAbierto, setMenuMovilAbierto] = useState(false);
  const navigate = useNavigate();

  const handleCerrarSesion = async () => {
    await cerrarSesion();
    navigate('/ingresar');
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

  return (
    <div className="min-h-screen flex bg-[#FAFAF9] dark:bg-[#0B0B0C] text-[#0B0B0C] dark:text-[#FAFAF9]">
      <ContenedorAvisos />

      {/* Backdrop móvil */}
      {menuMovilAbierto && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs md:hidden"
          onClick={() => setMenuMovilAbierto(false)}
        />
      )}

      {/* Barra Lateral (Sidebar) */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-50 h-screen w-64 bg-[#0B0B0C] text-[#FAFAF9] border-r border-[#2A2A2E] flex flex-col justify-between transition-transform duration-200 ease-in-out md:translate-x-0 ${
          menuMovilAbierto ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Encabezado Logo */}
        <div>
          <div className="px-6 py-6 border-b border-[#2A2A2E] flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 border border-[#C0C0C0] flex items-center justify-center rotate-45">
                  <div className="w-2.5 h-2.5 bg-[#C0C0C0] -rotate-45" />
                </div>
                <span className="font-serif-luxury text-xl tracking-[0.2em] font-medium text-white uppercase">
                  Aura
                </span>
              </div>
              <p className="text-[10px] tracking-[0.25em] text-[#8A8D91] uppercase mt-1">
                Apartaestudios · Colombia
              </p>
            </div>
            <button
              onClick={() => setMenuMovilAbierto(false)}
              className="p-1 md:hidden text-[#8A8D91] hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Menú de enlaces */}
          <nav className="p-4 space-y-1">
            <div className="px-3 py-2 text-[10px] tracking-[0.2em] uppercase text-[#8A8D91] font-semibold">
              Módulos Principales
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
                    `flex items-center gap-3 px-3 py-2.5 rounded-[4px] text-xs font-medium tracking-wide transition-all ${
                      isActive
                        ? 'bg-[#1A1A1D] text-[#FAFAF9] border-l-2 border-[#C0C0C0] pl-2.5 shadow-inner'
                        : 'text-[#8A8D91] hover:text-[#FAFAF9] hover:bg-[#141416]'
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

        {/* Sección inferior de usuario */}
        <div className="p-4 border-t border-[#2A2A2E] bg-[#0E0E10]">
          {usuario && (
            <div className="mb-3 px-2 py-1.5 flex items-center justify-between">
              <div className="overflow-hidden">
                <p className="text-xs font-medium text-white truncate">
                  {usuario.nombre}
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Shield className="w-3 h-3 text-[#8A8D91]" />
                  <span className="text-[10px] tracking-wider uppercase text-[#8A8D91]">
                    {usuario.rol}
                  </span>
                </div>
              </div>

              {/* Botón cambiar tema */}
              <button
                onClick={alternarTema}
                title={temaOscuro ? 'Modo claro' : 'Modo oscuro'}
                className="p-1.5 text-[#8A8D91] hover:text-[#C0C0C0] hover:bg-[#1A1A1D] rounded transition-colors"
                aria-label="Alternar tema"
              >
                {temaOscuro ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
            </div>
          )}

          <div className="space-y-1">
            <NavLink
              to="/cambiar-contrasena"
              onClick={() => setMenuMovilAbierto(false)}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 text-xs rounded-[4px] text-[#8A8D91] hover:text-white hover:bg-[#1A1A1D] transition-colors ${
                  isActive ? 'text-white bg-[#1A1A1D]' : ''
                }`
              }
            >
              <KeyRound className="w-4 h-4" />
              <span>Cambiar Contraseña</span>
            </NavLink>

            <button
              onClick={handleCerrarSesion}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs rounded-[4px] text-[#8A8D91] hover:text-[#E89AA3] hover:bg-[#7A1F2B]/10 transition-colors cursor-pointer text-left"
            >
              <LogOut className="w-4 h-4" />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Contenido Principal */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Barra Superior Móvil */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-[#0B0B0C] text-white border-b border-[#2A2A2E] sticky top-0 z-30">
          <button
            onClick={() => setMenuMovilAbierto(true)}
            className="p-1 text-[#8A8D91] hover:text-white"
            aria-label="Abrir menú de navegación"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border border-[#C0C0C0] rotate-45" />
            <span className="font-serif-luxury tracking-widest text-sm uppercase">Aura</span>
          </div>
          <button
            onClick={alternarTema}
            className="p-1 text-[#8A8D91]"
            aria-label="Alternar tema"
          >
            {temaOscuro ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </header>

        {/* Cuerpo de página */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
