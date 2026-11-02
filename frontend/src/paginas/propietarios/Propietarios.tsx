import React, { useEffect, useState, useCallback } from 'react';
import {
  listarPropietarios,
  obtenerPropietario,
  crearPropietario,
  actualizarPropietario,
  activarPropietario,
  desactivarPropietario,
} from '../../api/propietarios';
import {
  Propietario,
  PropietarioCrear,
  PropietarioDetalle,
  TipoDocumento,
  estadoApartaestudio,
} from '../../api/tipos';
import { Tabla, Columna } from '../../componentes/Tabla';
import { Boton } from '../../componentes/Boton';
import { Modal } from '../../componentes/Modal';
import { Campo, EntradaTexto, EntradaSeleccion } from '../../componentes/Campo';
import { InsigniaEstado } from '../../componentes/InsigniaEstado';
import { useAuth } from '../../contexto/AuthContext';
import { puede } from '../../utilidades/permisos';
import { ErrorApi } from '../../api/cliente';
import { vaciosANulo } from '../../utilidades/formato';
import { OpcionesDocumento } from '../../componentes/OpcionesDocumento';
import {
  Plus,
  Search,
  Eye,
  Edit2,
  Power,
  Building,
  Phone,
  Mail,
} from 'lucide-react';

interface FormularioPropietario {
  tipo_documento: TipoDocumento;
  numero_documento: string;
  nombre: string;
  telefono: string;
  correo: string;
  direccion: string;
  notas: string;
}

const FORMULARIO_VACIO: FormularioPropietario = {
    tipo_documento: 'CC',
    numero_documento: '',
    nombre: '',
    telefono: '',
    correo: '',
    direccion: '',
    notas: '',
  };

export const PaginaPropietarios: React.FC = () => {
  const [propietarios, setPropietarios] = useState<Propietario[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [terminoBusqueda, setTerminoBusqueda] = useState('');

  // Modales
  const [modalFormularioAbierto, setModalFormularioAbierto] = useState(false);
  const [modalDetalleAbierto, setModalDetalleAbierto] = useState(false);
  const [propietarioSeleccionado, setPropietarioSeleccionado] = useState<Propietario | null>(null);
  const [detallePropietario, setDetallePropietario] = useState<PropietarioDetalle | null>(null);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);

  // Formulario
  const [guardando, setGuardando] = useState(false);
  const [formulario, setFormulario] = useState<FormularioPropietario>(FORMULARIO_VACIO);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});

  const { agregarNotificacion, usuario } = useAuth();
  const puedeGestionar = puede(usuario, 'gestionar_propietarios');

  const cargarPropietarios = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await listarPropietarios({
        texto: terminoBusqueda.trim() || undefined,
      });
      setPropietarios(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar propietarios';
      setError(msg);
    } finally {
      setCargando(false);
    }
  }, [terminoBusqueda]);

  useEffect(() => {
    cargarPropietarios();
  }, [cargarPropietarios]);

  const abrirCrear = () => {
    setPropietarioSeleccionado(null);
    setFormulario(FORMULARIO_VACIO);
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirEditar = (p: Propietario) => {
    setPropietarioSeleccionado(p);
    setFormulario({
      tipo_documento: p.tipo_documento,
      numero_documento: p.numero_documento,
      nombre: p.nombre,
      telefono: p.telefono || '',
      correo: p.correo || '',
      direccion: p.direccion || '',
      notas: p.notas || '',
    });
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirDetalle = async (p: Propietario) => {
    setPropietarioSeleccionado(p);
    setModalDetalleAbierto(true);
    setCargandoDetalle(true);
    try {
      const detalle = await obtenerPropietario(p.id);
      setDetallePropietario(detalle);
    } catch {
      agregarNotificacion('error', 'Error al obtener detalle del propietario');
    } finally {
      setCargandoDetalle(false);
    }
  };

  const manejarAlternarEstado = async (p: Propietario) => {
    const accion = p.activo ? 'desactivar' : 'activar';
    const confirmacion = window.confirm(
      `¿Deseas ${accion} al propietario ${p.nombre}?`
    );
    if (!confirmacion) return;

    try {
      if (p.activo) {
        await desactivarPropietario(p.id);
        agregarNotificacion('info', `Propietario desactivado`);
      } else {
        await activarPropietario(p.id);
        agregarNotificacion('exito', `Propietario activado`);
      }
      cargarPropietarios();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al modificar estado';
      agregarNotificacion('error', msg);
    }
  };

  const guardarPropietario = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroresCampos({});

    // Validaciones en cliente
    const errs: Record<string, string> = {};
    if (!formulario.numero_documento.trim()) {
      errs.numero_documento = 'El número de documento es obligatorio';
    }
    if (!formulario.nombre.trim()) {
      errs.nombre = 'El nombre es obligatorio';
    }
    if (formulario.correo.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formulario.correo)) {
      errs.correo = 'Formato de correo inválido';
    }

    if (Object.keys(errs).length > 0) {
      setErroresCampos(errs);
      return;
    }

    setGuardando(true);
    try {
      if (propietarioSeleccionado) {
        await actualizarPropietario(propietarioSeleccionado.id, vaciosANulo(formulario));
        agregarNotificacion('exito', 'Propietario actualizado exitosamente');
      } else {
        await crearPropietario(vaciosANulo<PropietarioCrear>(formulario));
        agregarNotificacion('exito', 'Propietario registrado exitosamente');
      }
      setModalFormularioAbierto(false);
      cargarPropietarios();
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

  const columnas: Columna<Propietario>[] = [
    {
      clave: 'documento',
      encabezado: 'Documento',
      render: (p) => (
        <span className="font-medium text-xs">
          {p.tipo_documento} {p.numero_documento}
        </span>
      ),
    },
    {
      clave: 'nombre',
      encabezado: 'Nombre / Razón Social',
      render: (p) => (
        <div>
          <div className="font-medium text-sm text-tinta">
            {p.nombre}
          </div>
          <div className="text-xs text-tenue flex items-center gap-1">
            <Mail className="w-3 h-3" /> {p.correo || '—'}
          </div>
        </div>
      ),
    },
    {
      clave: 'telefono',
      encabezado: 'Teléfono',
      render: (p) => (
        <span className="text-xs text-tinta-2 flex items-center gap-1">
          <Phone className="w-3 h-3 text-tenue" /> {p.telefono || '—'}
        </span>
      ),
    },
    {
      clave: 'estado',
      encabezado: 'Estado',
      render: (p) => <InsigniaEstado tipo="activo" valor={p.activo} tamano="sm" />,
    },
    {
      clave: 'acciones',
      encabezado: 'Acciones',
      alineacion: 'derecha',
      render: (p) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => abrirDetalle(p)}
            title="Ver detalle e inmuebles"
            className="p-1.5 text-tinta-2 hover:text-tinta rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Eye className="w-4 h-4" />
          </button>
          {puedeGestionar && (<>
          <button
            onClick={() => abrirEditar(p)}
            title="Editar propietario"
            className="p-1.5 text-tinta-2 hover:text-tinta rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => manejarAlternarEstado(p)}
            title={p.activo ? 'Desactivar propietario' : 'Activar propietario'}
            className={`p-1.5 rounded transition-colors cursor-pointer ${
              p.activo
                ? 'text-peligro hover:bg-peligro/10'
                : 'text-exito hover:bg-exito/10'
            }`}
          >
            <Power className="w-4 h-4" />
          </button>
          </>)}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Cabecera de Página */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-linea">
        <div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-tenue">
            Directorio Inmobiliario
          </span>
          <h1 className="text-2xl sm:text-3xl font-titulo font-medium text-tinta mt-1">
            Propietarios
          </h1>
        </div>
        {puedeGestionar && (
          <Boton
            variante="plata"
            onClick={abrirCrear}
            icono={<Plus className="w-4 h-4" />}
          >
            Nuevo Propietario
          </Boton>
        )}
      </div>

      {/* Barra de Filtro y Búsqueda */}
      <div className="flex items-center gap-3 bg-panel p-3 rounded-lg border border-linea">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-tenue absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por nombre, documento o correo..."
            value={terminoBusqueda}
            onChange={(e) => setTerminoBusqueda(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-transparent border-0 outline-none text-tinta placeholder-tenue"
          />
        </div>
        {terminoBusqueda && (
          <button
            onClick={() => setTerminoBusqueda('')}
            className="text-xs text-tenue hover:text-tinta px-2 py-1"
          >
            Limpiar
          </button>
        )}
      </div>

      {/* Tabla */}
      <Tabla
        columnas={columnas}
        datos={propietarios}
        cargando={cargando}
        error={error}
        alReintentar={cargarPropietarios}
        mensajeVacio="No hay propietarios registrados"
        subtituloVacio="Registra tu primer propietario usando el botón 'Nuevo Propietario'."
      />

      {/* Modal Crear / Editar */}
      <Modal
        abierto={modalFormularioAbierto}
        alCerrar={() => setModalFormularioAbierto(false)}
        titulo={propietarioSeleccionado ? 'Editar Propietario' : 'Registrar Nuevo Propietario'}
        subtitulo="Ingresa los datos de identificación y contacto."
        tamano="lg"
      >
        <form onSubmit={guardarPropietario} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Campo
              label="Tipo Documento"
              obligatorio
              error={erroresCampos.tipo_documento}
              id="tipo_documento"
            >
              <EntradaSeleccion
                id="tipo_documento"
                value={formulario.tipo_documento}
                onChange={(e) =>
                  setFormulario({ ...formulario, tipo_documento: e.target.value as TipoDocumento })
                }
              >
                <OpcionesDocumento />
              </EntradaSeleccion>
            </Campo>

            <div className="sm:col-span-2">
              <Campo
                label="Número de Documento"
                obligatorio
                error={erroresCampos.numero_documento}
                id="numero_documento"
              >
                <EntradaTexto
                  id="numero_documento"
                  placeholder="ej. 1020304050"
                  value={formulario.numero_documento}
                  onChange={(e) =>
                    setFormulario({ ...formulario, numero_documento: e.target.value })
                  }
                  tieneError={Boolean(erroresCampos.numero_documento)}
                />
              </Campo>
            </div>
          </div>

          <Campo
            label="Nombre Completo / Razón Social"
            obligatorio
            error={erroresCampos.nombre}
            id="nombre"
          >
            <EntradaTexto
              id="nombre"
              placeholder="ej. Carlos Eduardo Restrepo Gómez"
              value={formulario.nombre}
              onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })}
              tieneError={Boolean(erroresCampos.nombre)}
            />
          </Campo>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Campo label="Teléfono / Celular" error={erroresCampos.telefono} id="telefono">
              <EntradaTexto
                id="telefono"
                placeholder="ej. 3101234567"
                value={formulario.telefono}
                onChange={(e) => setFormulario({ ...formulario, telefono: e.target.value })}
                tieneError={Boolean(erroresCampos.telefono)}
              />
            </Campo>

            <Campo
              label="Correo Electrónico"
              error={erroresCampos.correo}
              id="correo"
            >
              <EntradaTexto
                id="correo"
                type="email"
                placeholder="ej. propietario@correo.com"
                value={formulario.correo}
                onChange={(e) => setFormulario({ ...formulario, correo: e.target.value })}
                tieneError={Boolean(erroresCampos.correo)}
              />
            </Campo>
          </div>

          <Campo label="Dirección de Correspondencia" error={erroresCampos.direccion} id="direccion">
            <EntradaTexto
              id="direccion"
              placeholder="ej. Calle 85 # 14-20, Bogotá"
              value={formulario.direccion}
              onChange={(e) => setFormulario({ ...formulario, direccion: e.target.value })}
            />
          </Campo>

          <Campo label="Notas" error={erroresCampos.notas} id="notas">
            <EntradaTexto
              id="notas"
              placeholder="Observaciones internas (opcional)"
              value={formulario.notas}
              onChange={(e) => setFormulario({ ...formulario, notas: e.target.value })}
            />
          </Campo>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-linea">
            <Boton
              type="button"
              variante="fantasma"
              onClick={() => setModalFormularioAbierto(false)}
              disabled={guardando}
            >
              Cancelar
            </Boton>
            <Boton type="submit" variante="plata" cargando={guardando}>
              {propietarioSeleccionado ? 'Guardar Cambios' : 'Registrar Propietario'}
            </Boton>
          </div>
        </form>
      </Modal>

      {/* Modal Detalle con Apartaestudios */}
      <Modal
        abierto={modalDetalleAbierto}
        alCerrar={() => setModalDetalleAbierto(false)}
        titulo="Detalle del Propietario"
        subtitulo="Información personal y apartaestudios vinculados."
        tamano="lg"
      >
        {cargandoDetalle ? (
          <div className="py-12 text-center text-xs text-tenue uppercase tracking-wider">
            Cargando información del propietario...
          </div>
        ) : detallePropietario ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-fondo p-4 rounded-lg border border-linea">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-tenue">
                  Nombre / Documento
                </p>
                <p className="text-sm font-semibold text-tinta mt-0.5">
                  {detallePropietario.nombre}
                </p>
                <p className="text-xs text-tinta-2">
                  {detallePropietario.tipo_documento} {detallePropietario.numero_documento}
                </p>
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-widest text-tenue">Contacto</p>
                <p className="text-xs text-tinta mt-0.5">
                  Tel: {detallePropietario.telefono || '—'}
                </p>
                <p className="text-xs text-tinta-2">
                  Correo: {detallePropietario.correo || '—'}
                </p>
              </div>

              {detallePropietario.notas && (
                <div className="sm:col-span-2 pt-2 border-t border-linea">
                  <p className="text-[10px] uppercase tracking-widest text-tenue">Notas</p>
                  <p className="text-xs text-tinta mt-0.5">
                    {detallePropietario.notas}
                  </p>
                </div>
              )}
            </div>

            <div>
              <h4 className="font-titulo text-base font-medium text-tinta mb-3 flex items-center gap-2">
                <Building className="w-4 h-4 text-tenue" />
                Apartaestudios de su Propiedad ({detallePropietario.apartaestudios?.length || 0})
              </h4>

              {detallePropietario.apartaestudios &&
              detallePropietario.apartaestudios.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {detallePropietario.apartaestudios.map((ap) => (
                    <div
                      key={ap.id}
                      className="p-3 bg-panel border border-linea rounded-lg flex items-center justify-between"
                    >
                      <div>
                        <div className="text-xs font-semibold text-tinta">
                          Unidad {ap.codigo}
                        </div>
                        <div className="text-[11px] text-tenue">
                          {ap.direccion}
                        </div>
                      </div>
                      <InsigniaEstado tipo="apartaestudio" valor={estadoApartaestudio(ap)} tamano="sm" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-tenue bg-fondo rounded-lg border border-dashed border-linea-fuerte">
                  Este propietario no tiene apartaestudios registrados aún.
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <Boton
                variante="secundario"
                tamano="sm"
                onClick={() => setModalDetalleAbierto(false)}
              >
                Cerrar
              </Boton>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
};
