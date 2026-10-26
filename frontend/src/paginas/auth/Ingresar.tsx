import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexto/AuthContext';
import { Campo, EntradaTexto } from '../../componentes/Campo';
import { Boton } from '../../componentes/Boton';
import { ErrorApi } from '../../api/cliente';
import { Lock, User } from 'lucide-react';

export const PaginaIngresar: React.FC = () => {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [cargando, setCargando] = useState(false);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);

  const { iniciarSesion } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const destino = (location.state as { desde?: { pathname: string } })?.desde?.pathname || '/';

  const manejarEnvio = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroresCampos({});
    setErrorGeneral(null);

    // Validación cliente
    const nuevosErrores: Record<string, string> = {};
    if (!nombreUsuario.trim()) {
      nuevosErrores.nombre_usuario = 'El nombre de usuario es obligatorio';
    }
    if (!contrasena) {
      nuevosErrores.contrasena = 'La contraseña es obligatoria';
    }

    if (Object.keys(nuevosErrores).length > 0) {
      setErroresCampos(nuevosErrores);
      return;
    }

    setCargando(true);
    try {
      const usuarioLogueado = await iniciarSesion(nombreUsuario.trim(), contrasena);
      if (usuarioLogueado.debe_cambiar_contrasena) {
        navigate('/cambiar-contrasena', { replace: true });
      } else {
        navigate(destino, { replace: true });
      }
    } catch (err) {
      if (err instanceof ErrorApi) {
        setErrorGeneral(err.message);
        if (err.detalles && err.detalles.length > 0) {
          const mapa: Record<string, string> = {};
          err.detalles.forEach((d) => {
            mapa[d.campo] = d.mensaje;
          });
          setErroresCampos(mapa);
        }
      } else {
        setErrorGeneral('Error inesperado al conectar con el servidor.');
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#FAFAF9] dark:bg-[#0B0B0C] text-[#0B0B0C] dark:text-[#FAFAF9]">
      <div className="w-full max-w-md">
        {/* Logo de la marca */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 border border-[#C0C0C0] rotate-45 mb-4 bg-white dark:bg-[#141416] shadow-sm">
            <div className="w-5 h-5 bg-[#1A1A1D] dark:bg-[#C0C0C0] -rotate-45" />
          </div>
          <h1 className="font-serif-luxury text-3xl font-medium tracking-[0.15em] uppercase text-[#0B0B0C] dark:text-[#FAFAF9]">
            Aura
          </h1>
          <p className="text-xs tracking-[0.25em] uppercase text-[#8A8D91] mt-1 font-sans-clean">
            Administración de Apartaestudios
          </p>
          <div className="w-16 h-px bg-[#C0C0C0] mx-auto mt-4" />
        </div>

        {/* Tarjeta de login */}
        <div className="bg-white dark:bg-[#141416] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] p-8 shadow-sm">
          <div className="mb-6">
            <h2 className="text-lg font-medium text-[#1A1A1D] dark:text-[#FAFAF9]">
              Ingreso al Sistema
            </h2>
            <p className="text-xs text-[#8A8D91] mt-0.5">
              Acceso interno seguro para personal autorizado
            </p>
          </div>

          {errorGeneral && (
            <div className="mb-5 p-3.5 bg-[#FCF4F5] dark:bg-[#251013] border border-[#7A1F2B]/30 rounded-[4px] text-xs text-[#7A1F2B] dark:text-[#EFA3AC]">
              {errorGeneral}
            </div>
          )}

          <form onSubmit={manejarEnvio} className="space-y-4">
            <Campo
              label="Nombre de usuario"
              obligatorio
              error={erroresCampos.nombre_usuario}
              id="nombre_usuario"
            >
              <div className="relative">
                <EntradaTexto
                  id="nombre_usuario"
                  type="text"
                  autoComplete="username"
                  placeholder="ej. admin o empleado1"
                  value={nombreUsuario}
                  onChange={(e) => setNombreUsuario(e.target.value)}
                  tieneError={Boolean(erroresCampos.nombre_usuario)}
                  className="pl-9"
                  disabled={cargando}
                />
                <User className="w-4 h-4 text-[#8A8D91] absolute left-3 top-2.5 pointer-events-none" />
              </div>
            </Campo>

            <Campo
              label="Contraseña"
              obligatorio
              error={erroresCampos.contrasena}
              id="contrasena"
            >
              <div className="relative">
                <EntradaTexto
                  id="contrasena"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={contrasena}
                  onChange={(e) => setContrasena(e.target.value)}
                  tieneError={Boolean(erroresCampos.contrasena)}
                  className="pl-9"
                  disabled={cargando}
                />
                <Lock className="w-4 h-4 text-[#8A8D91] absolute left-3 top-2.5 pointer-events-none" />
              </div>
            </Campo>

            <div className="pt-2">
              <Boton
                type="submit"
                variante="plata"
                cargando={cargando}
                className="w-full py-2.5"
              >
                Ingresar al Portal
              </Boton>
            </div>
          </form>

          <div className="mt-6 pt-4 border-t border-[#E3E4E6] dark:border-[#2A2A2E] text-center">
            <p className="text-[11px] text-[#8A8D91]">
              Sesión protegida mediante credenciales corporativas y token CSRF
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
