import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexto/AuthContext';
import { Campo, EntradaTexto } from '../../componentes/Campo';
import { Boton } from '../../componentes/Boton';
import { ErrorApi } from '../../api/cliente';
import { ContenedorAvisos } from '../../componentes/Avisos';
import { Lock, User, Building2, ShieldCheck, Moon, Sun } from 'lucide-react';
import { FondoParticulas } from '../../componentes/FondoParticulas';

export const PaginaIngresar: React.FC = () => {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [cargando, setCargando] = useState(false);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);

  const { iniciarSesion, temaOscuro, alternarTema } = useAuth();
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
    <div className="relative min-h-screen flex items-center justify-center p-4 bg-fondo text-tinta overflow-hidden">
      <FondoParticulas />
      <ContenedorAvisos />

      {/* Brillo verde detrás de la tarjeta */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[520px] h-[520px] rounded-full opacity-60 blur-3xl"
        style={{ background: 'radial-gradient(circle, var(--c-acento-suave) 0%, transparent 70%)' }}
      />

      <button
        onClick={alternarTema}
        title={temaOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
        aria-label={temaOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
        className="absolute top-4 right-4 z-20 p-2.5 rounded-full bg-panel border border-linea text-tenue hover:text-acento-fuerte hover:border-acento transition-colors cursor-pointer"
      >
        {temaOscuro ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </button>

      <div className="relative z-10 w-full max-w-md">
        {/* Marca */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4 bg-acento-fuerte text-sobre-acento shadow-[0_12px_30px_-8px_var(--c-acento)]">
            <Building2 className="w-7 h-7" />
          </div>
          <h1 className="font-titulo text-4xl font-semibold tracking-tight text-tinta">
            Aura<span className="text-acento-fuerte">.</span>
          </h1>
          <p className="text-xs tracking-[0.25em] uppercase text-tenue mt-1.5">
            Administración de apartaestudios
          </p>
        </div>

        {/* Tarjeta de ingreso */}
        <div className="bg-panel border border-linea rounded-2xl p-8 shadow-[var(--sombra-elevada)]">
          <div className="mb-6">
            <h2 className="font-titulo text-xl font-semibold text-tinta">Ingreso al sistema</h2>
            <p className="text-sm text-tenue mt-1">Acceso interno para personal autorizado</p>
          </div>

          {errorGeneral && (
            <div className="mb-5 p-3.5 bg-peligro-bg border border-peligro/30 rounded-lg text-sm text-peligro">
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
                <User className="w-4 h-4 text-tenue absolute left-3 top-2.5 pointer-events-none" />
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
                <Lock className="w-4 h-4 text-tenue absolute left-3 top-2.5 pointer-events-none" />
              </div>
            </Campo>

            <div className="pt-2">
              <Boton type="submit" variante="primario" cargando={cargando} className="w-full py-2.5">
                Ingresar
              </Boton>
            </div>
          </form>

          <div className="mt-6 pt-4 border-t border-linea flex items-center justify-center gap-1.5 text-xs text-tenue">
            <ShieldCheck className="w-3.5 h-3.5 text-acento-fuerte" />
            <span>Sesión protegida con cookie segura y token CSRF</span>
          </div>
        </div>
      </div>
    </div>
  );
};
