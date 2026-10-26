import React, { useEffect, useState, useCallback } from 'react';
import {
  listarUsuarios,
  crearUsuario,
  actualizarUsuario,
  activarUsuario,
  desactivarUsuario,
  restablecerContrasenaUsuario,
} from '../../api/usuarios';
import { RolUsuario, Usuario, UsuarioCrear, UsuarioEditar } from '../../api/tipos';
import { vaciosANulo } from '../../utilidades/formato';
import { Tabla, Columna } from '../../componentes/Tabla';
import { Boton } from '../../componentes/Boton';
import { Modal } from '../../componentes/Modal';
import { Campo, EntradaTexto, EntradaSeleccion } from '../../componentes/Campo';
import { InsigniaEstado } from '../../componentes/InsigniaEstado';
import { useAuth } from '../../contexto/AuthContext';
import { ErrorApi } from '../../api/cliente';
import {
  Plus,
  Edit2,
  Power,
  KeyRound,
  Shield,
  UserCheck,
  Mail,
  User,
} from 'lucide-react';

export const PaginaUsuarios: React.FC = () => {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modales
  const [modalFormularioAbierto, setModalFormularioAbierto] = useState(false);
  const [modalRestablecerAbierto, setModalRestablecerAbierto] = useState(false);
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState<Usuario | null>(null);

  // Formulario Crear / Editar
  const [guardando, setGuardando] = useState(false);
  const [formulario, setFormulario] = useState<{
    nombre_usuario: string;
    nombre: string;
    correo: string;
    rol: RolUsuario;
    contrasena_temporal: string;
  }>({
    nombre_usuario: '',
    nombre: '',
    correo: '',
    rol: 'empleado',
    contrasena_temporal: '',
  });
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});

  // Restablecer contraseña
  const [nuevaContrasena, setNuevaContrasena] = useState('');
  const [errorRestablecer, setErrorRestablecer] = useState<string | null>(null);
  const [procesandoRestablecer, setProcesandoRestablecer] = useState(false);

  const { agregarNotificacion, usuario: usuarioActual } = useAuth();

  const cargarUsuarios = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await listarUsuarios();
      setUsuarios(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar usuarios';
      setError(msg);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarUsuarios();
  }, [cargarUsuarios]);

  const abrirCrear = () => {
    setUsuarioSeleccionado(null);
    setFormulario({
      nombre_usuario: '',
      nombre: '',
      correo: '',
      rol: 'empleado',
      contrasena_temporal: '',
    });
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirEditar = (u: Usuario) => {
    setUsuarioSeleccionado(u);
    setFormulario({
      nombre_usuario: u.nombre_usuario,
      nombre: u.nombre,
      correo: u.correo || '',
      rol: u.rol,
      contrasena_temporal: '',
    });
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirRestablecer = (u: Usuario) => {
    setUsuarioSeleccionado(u);
    setNuevaContrasena('');
    setErrorRestablecer(null);
    setModalRestablecerAbierto(true);
  };

  const manejarAlternarEstado = async (u: Usuario) => {
    if (u.id === usuarioActual?.id) {
      agregarNotificacion('advertencia', 'No puedes desactivar tu propia cuenta activa');
      return;
    }

    const accion = u.activo ? 'desactivar' : 'activar';
    if (!window.confirm(`¿Deseas ${accion} la cuenta de ${u.nombre}?`)) return;

    try {
      if (u.activo) {
        await desactivarUsuario(u.id);
        agregarNotificacion('info', `Usuario ${u.nombre_usuario} desactivado`);
      } else {
        await activarUsuario(u.id);
        agregarNotificacion('exito', `Usuario ${u.nombre_usuario} activado`);
      }
      cargarUsuarios();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al modificar estado';
      agregarNotificacion('error', msg);
    }
  };

  const guardarUsuario = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroresCampos({});

    const errs: Record<string, string> = {};
    if (!usuarioSeleccionado) {
      if (!formulario.nombre_usuario.trim() || formulario.nombre_usuario.length < 4) {
        errs.nombre_usuario = 'El nombre de usuario debe tener mínimo 4 caracteres';
      }
      if (formulario.contrasena_temporal.length < 10) {
        errs.contrasena_temporal = 'La contraseña temporal debe tener al menos 10 caracteres';
      }
    }
    if (!formulario.nombre.trim()) {
      errs.nombre = 'El nombre completo es obligatorio';
    }
    if (formulario.correo.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formulario.correo)) {
      errs.correo = 'Ingresa un correo válido';
    }

    if (Object.keys(errs).length > 0) {
      setErroresCampos(errs);
      return;
    }

    setGuardando(true);
    try {
      if (usuarioSeleccionado) {
        const datosEditar: UsuarioEditar = {
          nombre: formulario.nombre,
          correo: formulario.correo.trim() || null,
          rol: formulario.rol,
        };
        await actualizarUsuario(usuarioSeleccionado.id, datosEditar);
        agregarNotificacion('exito', 'Usuario actualizado correctamente');
      } else {
        await crearUsuario(vaciosANulo<UsuarioCrear>(formulario));
        agregarNotificacion('exito', 'Usuario creado correctamente');
      }
      setModalFormularioAbierto(false);
      cargarUsuarios();
    } catch (err) {
      if (err instanceof ErrorApi) {
        if (err.detalles && err.detalles.length > 0) {
          const mapa: Record<string, string> = {};
          err.detalles.forEach((d) => {
            mapa[d.campo] = d.mensaje;
          });
          setErroresCampos(mapa);
        }
      }
    } finally {
      setGuardando(false);
    }
  };

  const ejecutarRestablecer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usuarioSeleccionado) return;
    if (nuevaContrasena.length < 10) {
      setErrorRestablecer('La contraseña temporal debe tener al menos 10 caracteres');
      return;
    }

    setProcesandoRestablecer(true);
    try {
      await restablecerContrasenaUsuario(usuarioSeleccionado.id, nuevaContrasena);
      agregarNotificacion('exito', 'Contraseña temporal asignada; el usuario deberá cambiarla al ingresar');
      setModalRestablecerAbierto(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al restablecer contraseña';
      setErrorRestablecer(msg);
    } finally {
      setProcesandoRestablecer(false);
    }
  };

  const columnas: Columna<Usuario>[] = [
    {
      clave: 'usuario',
      encabezado: 'Usuario',
      render: (u) => (
        <div>
          <span className="font-semibold text-xs text-[#0B0B0C] dark:text-[#FAFAF9]">
            {u.nombre_usuario}
          </span>
          <p className="text-[11px] text-[#8A8D91]">{u.nombre}</p>
        </div>
      ),
    },
    {
      clave: 'correo',
      encabezado: 'Correo Corporativo',
      render: (u) => (
        <span className="text-xs text-[#5A5D62] dark:text-[#A0A3A8] flex items-center gap-1">
          <Mail className="w-3 h-3 text-[#8A8D91]" /> {u.correo || '—'}
        </span>
      ),
    },
    {
      clave: 'rol',
      encabezado: 'Rol del Sistema',
      render: (u) => <InsigniaEstado tipo="rol" valor={u.rol} tamano="sm" />,
    },
    {
      clave: 'estado',
      encabezado: 'Estado',
      render: (u) => <InsigniaEstado tipo="activo" valor={u.activo} tamano="sm" />,
    },
    {
      clave: 'acciones',
      encabezado: 'Acciones',
      alineacion: 'derecha',
      render: (u) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => abrirEditar(u)}
            title="Editar usuario"
            className="p-1.5 text-[#5A5D62] hover:text-[#0B0B0C] dark:text-[#A0A3A8] dark:hover:text-white rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => abrirRestablecer(u)}
            title="Restablecer contraseña"
            className="p-1.5 text-[#8A8D91] hover:text-[#1A1A1D] dark:hover:text-white rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <KeyRound className="w-4 h-4" />
          </button>
          <button
            onClick={() => manejarAlternarEstado(u)}
            disabled={u.id === usuarioActual?.id}
            title={u.activo ? 'Desactivar usuario' : 'Activar usuario'}
            className={`p-1.5 rounded transition-colors cursor-pointer disabled:opacity-30 ${
              u.activo ? 'text-[#7A1F2B] hover:bg-[#7A1F2B]/10' : 'text-[#2F4F4A] hover:bg-[#2F4F4A]/10'
            }`}
          >
            <Power className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-[#E3E4E6] dark:border-[#2A2A2E]">
        <div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-[#8A8D91]">
            Control de Accesos (Solo Administrador)
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
            Usuarios del Sistema
          </h1>
        </div>
        <Boton variante="plata" onClick={abrirCrear} icono={<Plus className="w-4 h-4" />}>
          Nuevo Usuario
        </Boton>
      </div>

      {/* Tabla */}
      <Tabla
        columnas={columnas}
        datos={usuarios}
        cargando={cargando}
        error={error}
        alReintentar={cargarUsuarios}
        mensajeVacio="No hay usuarios registrados"
        subtituloVacio="Agrega usuarios para autorizar a administradores o empleados."
      />

      {/* Modal Crear / Editar */}
      <Modal
        abierto={modalFormularioAbierto}
        alCerrar={() => setModalFormularioAbierto(false)}
        titulo={usuarioSeleccionado ? 'Editar Usuario' : 'Crear Usuario'}
        subtitulo="Asigna rol administrativo o de empleado con permisos específicos."
        tamano="md"
      >
        <form onSubmit={guardarUsuario} className="space-y-4">
          {!usuarioSeleccionado && (
            <Campo
              label="Nombre de usuario"
              obligatorio
              ayuda="Mínimo 4 caracteres"
              error={erroresCampos.nombre_usuario}
              id="usr_nombre"
            >
              <EntradaTexto
                id="usr_nombre"
                placeholder="ej. fsalazar"
                value={formulario.nombre_usuario}
                onChange={(e) =>
                  setFormulario({ ...formulario, nombre_usuario: e.target.value })
                }
                tieneError={Boolean(erroresCampos.nombre_usuario)}
              />
            </Campo>
          )}

          <Campo
            label="Nombre Completo"
            obligatorio
            error={erroresCampos.nombre}
            id="usr_completo"
          >
            <EntradaTexto
              id="usr_completo"
              placeholder="ej. Francisco Salazar Mejía"
              value={formulario.nombre}
              onChange={(e) =>
                setFormulario({ ...formulario, nombre: e.target.value })
              }
              tieneError={Boolean(erroresCampos.nombre)}
            />
          </Campo>

          <Campo label="Correo Corporativo" error={erroresCampos.correo} id="usr_email">
            <EntradaTexto
              id="usr_email"
              type="email"
              placeholder="ej. francisco@apartacolombia.com"
              value={formulario.correo}
              onChange={(e) => setFormulario({ ...formulario, correo: e.target.value })}
              tieneError={Boolean(erroresCampos.correo)}
            />
          </Campo>

          <Campo label="Rol en el Sistema" obligatorio id="usr_rol">
            <EntradaSeleccion
              id="usr_rol"
              value={formulario.rol}
              onChange={(e) =>
                setFormulario({ ...formulario, rol: e.target.value as RolUsuario })
              }
            >
              <option value="empleado">Empleado (Operación diaria, contratos, inmuebles)</option>
              <option value="administrador">Administrador (Acceso total, usuarios, auditoría)</option>
            </EntradaSeleccion>
          </Campo>

          {!usuarioSeleccionado && (
            <>
              <Campo
                label="Contraseña Temporal"
                obligatorio
                ayuda="Mínimo 10 caracteres"
                error={erroresCampos.contrasena_temporal}
                id="usr_pass"
              >
                <EntradaTexto
                  id="usr_pass"
                  type="password"
                  placeholder="••••••••"
                  value={formulario.contrasena_temporal}
                  onChange={(e) =>
                    setFormulario({ ...formulario, contrasena_temporal: e.target.value })
                  }
                  tieneError={Boolean(erroresCampos.contrasena_temporal)}
                />
              </Campo>

              <p className="text-[11px] text-[#8A8D91] pt-1">
                El usuario deberá cambiar esta contraseña en su primer ingreso.
              </p>
            </>
          )}

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-[#E3E4E6] dark:border-[#2A2A2E]">
            <Boton
              type="button"
              variante="fantasma"
              onClick={() => setModalFormularioAbierto(false)}
              disabled={guardando}
            >
              Cancelar
            </Boton>
            <Boton type="submit" variante="plata" cargando={guardando}>
              {usuarioSeleccionado ? 'Guardar Cambios' : 'Crear Usuario'}
            </Boton>
          </div>
        </form>
      </Modal>

      {/* Modal Restablecer Contraseña */}
      <Modal
        abierto={modalRestablecerAbierto}
        alCerrar={() => setModalRestablecerAbierto(false)}
        titulo={`Restablecer Contraseña · ${usuarioSeleccionado?.nombre_usuario}`}
        subtitulo="Asigna una nueva clave para este usuario de acceso."
        tamano="sm"
      >
        <form onSubmit={ejecutarRestablecer} className="space-y-4">
          {errorRestablecer && (
            <div className="p-3 bg-[#FCF4F5] dark:bg-[#251013] border border-[#7A1F2B]/40 rounded text-xs text-[#7A1F2B] dark:text-[#EFA3AC]">
              {errorRestablecer}
            </div>
          )}

          <Campo
            label="Nueva Contraseña"
            obligatorio
            ayuda="Mínimo 10 caracteres"
            id="rest_pass"
          >
            <EntradaTexto
              id="rest_pass"
              type="password"
              placeholder="••••••••"
              value={nuevaContrasena}
              onChange={(e) => setNuevaContrasena(e.target.value)}
              disabled={procesandoRestablecer}
            />
          </Campo>

          <div className="pt-3 flex items-center justify-end gap-2 border-t border-[#E3E4E6] dark:border-[#2A2A2E]">
            <Boton
              type="button"
              variante="fantasma"
              onClick={() => setModalRestablecerAbierto(false)}
              disabled={procesandoRestablecer}
            >
              Cancelar
            </Boton>
            <Boton
              type="submit"
              variante="plata"
              cargando={procesandoRestablecer}
              icono={<KeyRound className="w-4 h-4" />}
            >
              Restablecer Clave
            </Boton>
          </div>
        </form>
      </Modal>
    </div>
  );
};
