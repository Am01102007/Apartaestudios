import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexto/AuthContext';
import { cambiarContrasena } from '../../api/auth';
import { Campo, EntradaTexto } from '../../componentes/Campo';
import { Boton } from '../../componentes/Boton';
import { ErrorApi } from '../../api/cliente';
import { KeyRound, ShieldAlert } from 'lucide-react';

export const PaginaCambiarContrasena: React.FC = () => {
  const { usuario, debeCambiarContrasena, refrescarSesion, agregarNotificacion } = useAuth();
  const [contrasenaActual, setContrasenaActual] = useState('');
  const [nuevaContrasena, setNuevaContrasena] = useState('');
  const [confirmarContrasena, setConfirmarContrasena] = useState('');
  const [cargando, setCargando] = useState(false);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);

  const navigate = useNavigate();

  const manejarEnvio = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroresCampos({});
    setErrorGeneral(null);

    const nuevosErrores: Record<string, string> = {};
    if (!contrasenaActual) {
      nuevosErrores.contrasena_actual = 'Ingresa tu contraseña actual';
    }
    if (!nuevaContrasena) {
      nuevosErrores.nueva_contrasena = 'La nueva contraseña es obligatoria';
    } else if (nuevaContrasena.length < 10) {
      nuevosErrores.nueva_contrasena = 'La contraseña debe tener al menos 10 caracteres';
    }
    if (nuevaContrasena !== confirmarContrasena) {
      nuevosErrores.confirmar_contrasena = 'Las contraseñas no coinciden';
    }

    if (Object.keys(nuevosErrores).length > 0) {
      setErroresCampos(nuevosErrores);
      return;
    }

    setCargando(true);
    try {
      await cambiarContrasena(contrasenaActual, nuevaContrasena);
      agregarNotificacion('exito', 'Contraseña actualizada correctamente');
      await refrescarSesion();
      navigate('/', { replace: true });
    } catch (err) {
      if (err instanceof ErrorApi) {
        setErrorGeneral(err.message);
        if (err.detalles && err.detalles.length > 0) {
          const mapa: Record<string, string> = {};
          err.detalles.forEach((d) => {
            mapa[d.campo === 'contrasena_nueva' ? 'nueva_contrasena' : d.campo] = d.mensaje;
          });
          setErroresCampos(mapa);
        }
      } else {
        setErrorGeneral('Ocurrió un error al intentar cambiar la contraseña');
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-8">
      <div className="bg-white dark:bg-[#141416] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[#E3E4E6] dark:border-[#2A2A2E]">
          <div className="w-10 h-10 rounded-[4px] bg-[#F4F5F6] dark:bg-[#1A1A1D] border border-[#C0C0C0] dark:border-[#3A3A3E] flex items-center justify-center text-[#1A1A1D] dark:text-[#FAFAF9]">
            <KeyRound className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9]">
              Cambio de Contraseña
            </h1>
            <p className="text-xs text-[#8A8D91]">
              Usuario: <span className="font-semibold text-current">{usuario?.nombre_usuario}</span>
            </p>
          </div>
        </div>

        {debeCambiarContrasena && (
          <div className="mb-6 p-4 bg-[#FAF6EE] dark:bg-[#241F14] border border-[#805B10]/30 rounded-[4px] flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-[#805B10] shrink-0 mt-0.5" />
            <div className="text-xs text-[#805B10] dark:text-[#E8C576] leading-relaxed">
              <span className="font-semibold block mb-0.5">Cambio de contraseña requerido:</span>
              Por políticas de seguridad interna, debes actualizar tu contraseña temporal antes de poder acceder a los módulos del sistema.
            </div>
          </div>
        )}

        {errorGeneral && (
          <div className="mb-5 p-3.5 bg-[#FCF4F5] dark:bg-[#251013] border border-[#7A1F2B]/30 rounded-[4px] text-xs text-[#7A1F2B] dark:text-[#EFA3AC]">
            {errorGeneral}
          </div>
        )}

        <form onSubmit={manejarEnvio} className="space-y-4">
          <Campo
            label="Contraseña actual"
            obligatorio
            error={erroresCampos.contrasena_actual}
            id="contrasena_actual"
          >
            <EntradaTexto
              id="contrasena_actual"
              type="password"
              value={contrasenaActual}
              onChange={(e) => setContrasenaActual(e.target.value)}
              tieneError={Boolean(erroresCampos.contrasena_actual)}
              disabled={cargando}
              placeholder="••••••••"
            />
          </Campo>

          <Campo
            label="Nueva contraseña"
            obligatorio
            ayuda="Mínimo 10 caracteres"
            error={erroresCampos.nueva_contrasena}
            id="nueva_contrasena"
          >
            <EntradaTexto
              id="nueva_contrasena"
              type="password"
              value={nuevaContrasena}
              onChange={(e) => setNuevaContrasena(e.target.value)}
              tieneError={Boolean(erroresCampos.nueva_contrasena)}
              disabled={cargando}
              placeholder="••••••••"
            />
          </Campo>

          <Campo
            label="Confirmar nueva contraseña"
            obligatorio
            error={erroresCampos.confirmar_contrasena}
            id="confirmar_contrasena"
          >
            <EntradaTexto
              id="confirmar_contrasena"
              type="password"
              value={confirmarContrasena}
              onChange={(e) => setConfirmarContrasena(e.target.value)}
              tieneError={Boolean(erroresCampos.confirmar_contrasena)}
              disabled={cargando}
              placeholder="••••••••"
            />
          </Campo>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-[#E3E4E6] dark:border-[#2A2A2E]">
            {!debeCambiarContrasena && (
              <Boton
                type="button"
                variante="fantasma"
                onClick={() => navigate(-1)}
                disabled={cargando}
              >
                Cancelar
              </Boton>
            )}
            <Boton type="submit" variante="plata" cargando={cargando}>
              Actualizar Contraseña
            </Boton>
          </div>
        </form>
      </div>
    </div>
  );
};
