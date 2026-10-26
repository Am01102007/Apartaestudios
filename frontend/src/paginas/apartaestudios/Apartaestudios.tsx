import React, { useEffect, useState, useCallback } from 'react';
import {
  listarApartaestudios,
  obtenerApartaestudio,
  crearApartaestudio,
  actualizarApartaestudio,
  obtenerContratosApartaestudio,
  cambiarMantenimiento,
  activarApartaestudio,
  desactivarApartaestudio,
} from '../../api/apartaestudios';
import { listarPropietarios } from '../../api/propietarios';
import {
  Apartaestudio,
  ApartaestudioCrear,
  Contrato,
  EstadoApartaestudio,
  Propietario,
  estadoApartaestudio,
} from '../../api/tipos';
import { Tabla, Columna } from '../../componentes/Tabla';
import { Boton } from '../../componentes/Boton';
import { Modal } from '../../componentes/Modal';
import { Campo, EntradaTexto, EntradaSeleccion, EntradaAreaTexto } from '../../componentes/Campo';
import { InsigniaEstado } from '../../componentes/InsigniaEstado';
import { useAuth } from '../../contexto/AuthContext';
import { ErrorApi } from '../../api/cliente';
import { formatearMonedaCOP, formatearFechaCO, vaciosANulo } from '../../utilidades/formato';
import {
  Plus,
  Search,
  Eye,
  Edit2,
  Wrench,
  CheckCircle,
  Power,
  Building2,
  Filter,
} from 'lucide-react';

interface FormularioApartaestudio {
  codigo: string;
  propietario_id: string;
  direccion: string;
  area_m2: string;
  descripcion: string;
}

const FORMULARIO_VACIO: FormularioApartaestudio = {
  codigo: '',
  propietario_id: '',
  direccion: '',
  area_m2: '',
  descripcion: '',
};

export const PaginaApartaestudios: React.FC = () => {
  const [apartaestudios, setApartaestudios] = useState<Apartaestudio[]>([]);
  const [propietarios, setPropietarios] = useState<Propietario[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [filtroEstado, setFiltroEstado] = useState<EstadoApartaestudio | ''>('');
  const [filtroPropietario, setFiltroPropietario] = useState<string>('');
  const [busqueda, setBusqueda] = useState<string>('');

  // Modales
  const [modalFormularioAbierto, setModalFormularioAbierto] = useState(false);
  const [modalDetalleAbierto, setModalDetalleAbierto] = useState(false);
  const [modalMantenimientoAbierto, setModalMantenimientoAbierto] = useState(false);

  // Seleccionados
  const [apartaestudioSeleccionado, setApartaestudioSeleccionado] = useState<Apartaestudio | null>(null);
  const [contratosApartaestudio, setContratosApartaestudio] = useState<Contrato[]>([]);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);

  // Mantenimiento
  const [motivoMantenimiento, setMotivoMantenimiento] = useState('');
  const [errorMantenimiento, setErrorMantenimiento] = useState<string | null>(null);
  const [procesandoMantenimiento, setProcesandoMantenimiento] = useState(false);

  // Formulario Crear / Editar
  const [guardando, setGuardando] = useState(false);
  const [formulario, setFormulario] = useState<FormularioApartaestudio>(FORMULARIO_VACIO);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});

  const { agregarNotificacion } = useAuth();

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [respAparta, respProp] = await Promise.all([
        listarApartaestudios({
          ocupacion: filtroEstado && filtroEstado !== 'mantenimiento' ? filtroEstado : undefined,
          en_mantenimiento: filtroEstado === '' ? undefined : filtroEstado === 'mantenimiento',
          propietario_id: filtroPropietario ? Number(filtroPropietario) : undefined,
          texto: busqueda.trim() || undefined,
        }),
        listarPropietarios(),
      ]);
      setApartaestudios(respAparta);
      setPropietarios(respProp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar apartaestudios';
      setError(msg);
    } finally {
      setCargando(false);
    }
  }, [filtroEstado, filtroPropietario, busqueda]);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  const abrirCrear = () => {
    setApartaestudioSeleccionado(null);
    setFormulario({
      ...FORMULARIO_VACIO,
      propietario_id: String(propietarios.find((p) => p.activo)?.id ?? ''),
    });
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirEditar = (a: Apartaestudio) => {
    setApartaestudioSeleccionado(a);
    setFormulario({
      codigo: a.codigo,
      propietario_id: String(a.propietario.id),
      direccion: a.direccion,
      area_m2: a.area_m2 ? String(Number(a.area_m2)) : '',
      descripcion: a.descripcion || '',
    });
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirDetalle = async (a: Apartaestudio) => {
    setApartaestudioSeleccionado(a);
    setModalDetalleAbierto(true);
    setCargandoDetalle(true);
    try {
      const [detalleActualizado, listaContratos] = await Promise.all([
        obtenerApartaestudio(a.id),
        obtenerContratosApartaestudio(a.id),
      ]);
      setApartaestudioSeleccionado(detalleActualizado);
      setContratosApartaestudio(listaContratos);
    } catch {
      agregarNotificacion('error', 'Error al cargar contratos del apartaestudio');
    } finally {
      setCargandoDetalle(false);
    }
  };

  const abrirModalMantenimiento = (a: Apartaestudio) => {
    setApartaestudioSeleccionado(a);
    setMotivoMantenimiento('');
    setErrorMantenimiento(null);
    setModalMantenimientoAbierto(true);
  };

  const enviarMantenimiento = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apartaestudioSeleccionado) return;
    if (motivoMantenimiento.trim().length < 3) {
      setErrorMantenimiento('El motivo debe tener al menos 3 caracteres');
      return;
    }

    setProcesandoMantenimiento(true);
    try {
      const activar = !apartaestudioSeleccionado.en_mantenimiento;
      await cambiarMantenimiento(apartaestudioSeleccionado.id, activar, motivoMantenimiento.trim());
      agregarNotificacion(
        'info',
        activar
          ? `Unidad ${apartaestudioSeleccionado.codigo} puesta en mantenimiento`
          : `Unidad ${apartaestudioSeleccionado.codigo} sale de mantenimiento`
      );
      setModalMantenimientoAbierto(false);
      cargarDatos();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al ingresar a mantenimiento';
      setErrorMantenimiento(msg);
    } finally {
      setProcesandoMantenimiento(false);
    }
  };

  const manejarAlternarEstado = async (a: Apartaestudio) => {
    const accion = a.activo ? 'desactivar' : 'activar';
    if (!window.confirm(`¿Seguro que deseas ${accion} el apartaestudio ${a.codigo}?`)) return;

    try {
      if (a.activo) {
        await desactivarApartaestudio(a.id);
        agregarNotificacion('info', `Apartaestudio ${a.codigo} desactivado`);
      } else {
        await activarApartaestudio(a.id);
        agregarNotificacion('exito', `Apartaestudio ${a.codigo} activado`);
      }
      cargarDatos();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cambiar estado';
      agregarNotificacion('error', msg);
    }
  };

  const guardarApartaestudio = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroresCampos({});

    const errs: Record<string, string> = {};
    if (!formulario.codigo.trim()) errs.codigo = 'El código del apartaestudio es obligatorio';
    if (!formulario.propietario_id) errs.propietario_id = 'Debes seleccionar un propietario';
    if (!formulario.direccion.trim()) errs.direccion = 'La dirección es obligatoria';
    if (formulario.area_m2 && !(Number(formulario.area_m2) > 0)) {
      errs.area_m2 = 'Ingresa un área válida en m²';
    }

    if (Object.keys(errs).length > 0) {
      setErroresCampos(errs);
      return;
    }

    setGuardando(true);
    try {
      const datos = vaciosANulo<ApartaestudioCrear>({
        ...formulario,
        propietario_id: Number(formulario.propietario_id),
      });
      if (apartaestudioSeleccionado) {
        await actualizarApartaestudio(apartaestudioSeleccionado.id, datos);
        agregarNotificacion('exito', `Unidad ${formulario.codigo} actualizada con éxito`);
      } else {
        await crearApartaestudio(datos);
        agregarNotificacion('exito', `Unidad ${formulario.codigo} creada con éxito`);
      }
      setModalFormularioAbierto(false);
      cargarDatos();
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

  const columnas: Columna<Apartaestudio>[] = [
    {
      clave: 'numero',
      encabezado: 'Apartaestudio',
      render: (a) => (
        <div>
          <span className="font-semibold text-sm text-[#0B0B0C] dark:text-[#FAFAF9]">
            Apto {a.codigo}
          </span>
          <p className="text-[11px] text-[#8A8D91]">
            {a.direccion}
            {a.area_m2 ? ` · ${Number(a.area_m2)} m²` : ''}
          </p>
        </div>
      ),
    },
    {
      clave: 'propietario',
      encabezado: 'Propietario',
      render: (a) => (
        <span className="text-xs text-[#1A1A1D] dark:text-[#FAFAF9] font-medium">
          {a.propietario.nombre}
        </span>
      ),
    },
    {
      clave: 'estado',
      encabezado: 'Estado de Ocupación',
      render: (a) => (
        <div className="flex flex-col gap-1 items-start">
          <InsigniaEstado tipo="apartaestudio" valor={estadoApartaestudio(a)} tamano="sm" />
          {a.en_mantenimiento && a.mantenimiento_motivo && (
            <span className="text-[10px] text-[#8A8D91] italic max-w-xs truncate" title={a.mantenimiento_motivo}>
              Motivo: {a.mantenimiento_motivo}
            </span>
          )}
        </div>
      ),
    },
    {
      clave: 'activo',
      encabezado: 'Disponibilidad',
      render: (a) => <InsigniaEstado tipo="activo" valor={a.activo} tamano="sm" />,
    },
    {
      clave: 'acciones',
      encabezado: 'Acciones',
      alineacion: 'derecha',
      render: (a) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => abrirDetalle(a)}
            title="Ver ocupación y contratos"
            className="p-1.5 text-[#5A5D62] hover:text-[#0B0B0C] dark:text-[#A0A3A8] dark:hover:text-white rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => abrirEditar(a)}
            title="Editar inmueble"
            className="p-1.5 text-[#5A5D62] hover:text-[#0B0B0C] dark:text-[#A0A3A8] dark:hover:text-white rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Edit2 className="w-4 h-4" />
          </button>

          {/* Marcar o retirar mantenimiento */}
          {a.activo && (
            <button
              onClick={() => abrirModalMantenimiento(a)}
              title={a.en_mantenimiento ? 'Retirar mantenimiento' : 'Marcar mantenimiento'}
              className={`p-1.5 rounded transition-colors cursor-pointer ${
                a.en_mantenimiento
                  ? 'text-[#2F4F4A] hover:bg-[#2F4F4A]/10'
                  : 'text-[#8A8D91] hover:text-[#1A1A1D] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              {a.en_mantenimiento ? <CheckCircle className="w-4 h-4" /> : <Wrench className="w-4 h-4" />}
            </button>
          )}

          <button
            onClick={() => manejarAlternarEstado(a)}
            title={a.activo ? 'Desactivar apartaestudio' : 'Activar apartaestudio'}
            className={`p-1.5 rounded transition-colors cursor-pointer ${
              a.activo ? 'text-[#7A1F2B] hover:bg-[#7A1F2B]/10' : 'text-[#2F4F4A] hover:bg-[#2F4F4A]/10'
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
            Inventario Inmobiliario
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
            Apartaestudios
          </h1>
        </div>
        <Boton variante="plata" onClick={abrirCrear} icono={<Plus className="w-4 h-4" />}>
          Nuevo Apartaestudio
        </Boton>
      </div>

      {/* Filtros solicitados: por estado de ocupación y propietario, más búsqueda */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-white dark:bg-[#141416] p-4 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
        <div className="relative sm:col-span-2">
          <Search className="w-4 h-4 text-[#8A8D91] absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por código o dirección..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
          />
        </div>

        <div>
          <select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value as EstadoApartaestudio | '')}
            className="w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
          >
            <option value="">Todos los estados</option>
            <option value="libre">Libre</option>
            <option value="ocupado">Ocupado</option>
            <option value="mantenimiento">Mantenimiento</option>
          </select>
        </div>

        <div>
          <select
            value={filtroPropietario}
            onChange={(e) => setFiltroPropietario(e.target.value)}
            className="w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
          >
            <option value="">Todos los propietarios</option>
            {propietarios.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabla */}
      <Tabla
        columnas={columnas}
        datos={apartaestudios}
        cargando={cargando}
        error={error}
        alReintentar={cargarDatos}
        mensajeVacio="No se encontraron apartaestudios"
        subtituloVacio="Ajusta los filtros o agrega una nueva unidad inmobiliaria."
      />

      {/* Modal Crear / Editar */}
      <Modal
        abierto={modalFormularioAbierto}
        alCerrar={() => setModalFormularioAbierto(false)}
        titulo={apartaestudioSeleccionado ? 'Editar Apartaestudio' : 'Nuevo Apartaestudio'}
        subtitulo="Código, dirección, área y propietario asignado."
        tamano="lg"
      >
        <form onSubmit={guardarApartaestudio} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Campo label="Código" obligatorio error={erroresCampos.codigo} id="codigo">
              <EntradaTexto
                id="codigo"
                placeholder="ej. A-302"
                value={formulario.codigo}
                onChange={(e) => setFormulario({ ...formulario, codigo: e.target.value })}
                tieneError={Boolean(erroresCampos.codigo)}
              />
            </Campo>

            <Campo
              label="Propietario del Inmueble"
              obligatorio
              error={erroresCampos.propietario_id}
              id="propietario_id"
            >
              <EntradaSeleccion
                id="propietario_id"
                value={formulario.propietario_id}
                onChange={(e) => setFormulario({ ...formulario, propietario_id: e.target.value })}
                tieneError={Boolean(erroresCampos.propietario_id)}
              >
                <option value="">Selecciona un propietario</option>
                {propietarios
                  .filter((p) => p.activo || String(p.id) === formulario.propietario_id)
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} ({p.tipo_documento} {p.numero_documento})
                    </option>
                  ))}
              </EntradaSeleccion>
            </Campo>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <Campo label="Dirección" obligatorio error={erroresCampos.direccion} id="direccion">
                <EntradaTexto
                  id="direccion"
                  placeholder="ej. Calle 45 # 12-30, apto 302"
                  value={formulario.direccion}
                  onChange={(e) => setFormulario({ ...formulario, direccion: e.target.value })}
                  tieneError={Boolean(erroresCampos.direccion)}
                />
              </Campo>
            </div>

            <Campo label="Área (m²)" error={erroresCampos.area_m2} id="area_m2">
              <EntradaTexto
                id="area_m2"
                type="number"
                step="0.01"
                min="0"
                value={formulario.area_m2}
                onChange={(e) => setFormulario({ ...formulario, area_m2: e.target.value })}
                tieneError={Boolean(erroresCampos.area_m2)}
              />
            </Campo>
          </div>

          <Campo label="Descripción y Acabados" id="descripcion">
            <EntradaAreaTexto
              id="descripcion"
              placeholder="ej. Cocina integral, closet empotrado, vista exterior, calentador a gas."
              value={formulario.descripcion}
              onChange={(e) => setFormulario({ ...formulario, descripcion: e.target.value })}
            />
          </Campo>

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
              {apartaestudioSeleccionado ? 'Guardar Cambios' : 'Crear Apartaestudio'}
            </Boton>
          </div>
        </form>
      </Modal>

      {/* Modal Marcar Mantenimiento (pide motivo obligatorio) */}
      <Modal
        abierto={modalMantenimientoAbierto}
        alCerrar={() => setModalMantenimientoAbierto(false)}
        titulo={`${apartaestudioSeleccionado?.en_mantenimiento ? 'Retirar' : 'Poner en'} Mantenimiento · Unidad ${apartaestudioSeleccionado?.codigo}`}
        subtitulo="El motivo queda registrado en la auditoría."
        tamano="sm"
      >
        <form onSubmit={enviarMantenimiento} className="space-y-4">
          {errorMantenimiento && (
            <div className="p-3 bg-[#FCF4F5] dark:bg-[#251013] border border-[#7A1F2B]/40 rounded text-xs text-[#7A1F2B] dark:text-[#EFA3AC]">
              {errorMantenimiento}
            </div>
          )}

          <Campo
            label="Motivo"
            obligatorio
            ayuda="Entre 3 y 300 caracteres"
            id="motivo_mantenimiento"
          >
            <EntradaAreaTexto
              id="motivo_mantenimiento"
              placeholder="ej. Reparación de fuga en baño principal y pintura general de paredes."
              value={motivoMantenimiento}
              onChange={(e) => setMotivoMantenimiento(e.target.value)}
              disabled={procesandoMantenimiento}
              rows={4}
            />
          </Campo>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#E3E4E6] dark:border-[#2A2A2E]">
            <Boton
              type="button"
              variante="fantasma"
              onClick={() => setModalMantenimientoAbierto(false)}
              disabled={procesandoMantenimiento}
            >
              Cancelar
            </Boton>
            <Boton
              type="submit"
              variante="peligro"
              cargando={procesandoMantenimiento}
              icono={<Wrench className="w-4 h-4" />}
            >
              {apartaestudioSeleccionado?.en_mantenimiento ? 'Retirar Mantenimiento' : 'Confirmar Mantenimiento'}
            </Boton>
          </div>
        </form>
      </Modal>

      {/* Modal Detalle con Contratos */}
      <Modal
        abierto={modalDetalleAbierto}
        alCerrar={() => setModalDetalleAbierto(false)}
        titulo={`Apartaestudio ${apartaestudioSeleccionado?.codigo} · Detalle y Contratos`}
        subtitulo="Histórico de arrendamiento, contratos vinculados y estado actual."
        tamano="lg"
      >
        {cargandoDetalle ? (
          <div className="py-12 text-center text-xs text-[#8A8D91] uppercase tracking-wider">
            Cargando historial de contratos...
          </div>
        ) : apartaestudioSeleccionado ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-[#FAFAF9] dark:bg-[#1A1A1D] p-4 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">Estado Actual</p>
                <div className="mt-1">
                  <InsigniaEstado
                    tipo="apartaestudio"
                    valor={estadoApartaestudio(apartaestudioSeleccionado)}
                    tamano="md"
                  />
                </div>
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">Dirección</p>
                <p className="text-xs font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
                  {apartaestudioSeleccionado.direccion}
                  {apartaestudioSeleccionado.area_m2
                    ? ` · ${Number(apartaestudioSeleccionado.area_m2)} m²`
                    : ''}
                </p>
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">Propietario</p>
                <p className="text-xs font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
                  {apartaestudioSeleccionado.propietario.nombre}
                </p>
              </div>

              {apartaestudioSeleccionado.descripcion && (
                <div className="sm:col-span-3 pt-2 border-t border-[#E3E4E6] dark:border-[#2A2A2E]">
                  <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">Descripción</p>
                  <p className="text-xs text-[#5A5D62] dark:text-[#A0A3A8] mt-0.5">
                    {apartaestudioSeleccionado.descripcion}
                  </p>
                </div>
              )}
            </div>

            {/* Listado de Contratos */}
            <div>
              <h4 className="font-serif-luxury text-base font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mb-3">
                Historial de Contratos Vinculados ({contratosApartaestudio.length})
              </h4>

              {contratosApartaestudio.length > 0 ? (
                <div className="divide-y divide-[#E3E4E6] dark:divide-[#2A2A2E] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] overflow-hidden bg-white dark:bg-[#141416]">
                  {contratosApartaestudio.map((c) => (
                    <div key={c.id} className="p-3.5 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-[#0B0B0C] dark:text-[#FAFAF9]">
                            Contrato #{c.id}
                          </span>
                          <span className="text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
                            · Residente: {c.residente.nombre}
                          </span>
                        </div>
                        <div className="text-[11px] text-[#8A8D91] mt-0.5">
                          Vigencia: {formatearFechaCO(c.fecha_inicio)} al {formatearFechaCO(c.fecha_terminacion)} · Canon: {formatearMonedaCOP(c.canon_vigente)}
                        </div>
                      </div>
                      <InsigniaEstado tipo="contrato" valor={c.estado} tamano="sm" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-[#8A8D91] bg-[#FAFAF9] dark:bg-[#1A1A1D] rounded-[4px] border border-dashed border-[#C0C0C0] dark:border-[#3A3A3E]">
                  No se registran contratos anteriores para este apartaestudio.
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
