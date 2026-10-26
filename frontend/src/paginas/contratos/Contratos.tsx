import React, { useEffect, useState, useCallback } from 'react';
import {
  listarContratos,
  obtenerContrato,
  crearContrato,
  actualizarContrato,
  obtenerHistorialContrato,
  prorrogarContrato,
  renovarContrato,
  terminarContrato,
  anularContrato,
} from '../../api/contratos';
import { listarApartaestudios } from '../../api/apartaestudios';
import { listarResidentes } from '../../api/residentes';
import {
  Apartaestudio,
  CambioContrato,
  Contrato,
  ContratoDetalle,
  ContratoEditar,
  EstadoContrato,
  ESTADOS_CONTRATO,
  NOMBRES_ESTADO_CONTRATO,
  Residente,
  estadoApartaestudio,
} from '../../api/tipos';
import { Tabla, Columna } from '../../componentes/Tabla';
import { Boton } from '../../componentes/Boton';
import { Modal } from '../../componentes/Modal';
import { Campo, EntradaTexto, EntradaSeleccion, EntradaAreaTexto } from '../../componentes/Campo';
import { InsigniaEstado } from '../../componentes/InsigniaEstado';
import { useAuth } from '../../contexto/AuthContext';
import { ErrorApi } from '../../api/cliente';
import {
  formatearFechaCO,
  formatearFechaHoraCO,
  formatearMonedaCOP,
  obtenerFechaHoyCO,
} from '../../utilidades/formato';
import {
  Plus,
  Edit2,
  CalendarPlus,
  RotateCw,
  XCircle,
  Ban,
  History,
  AlertCircle,
  User,
} from 'lucide-react';

// Qué permite el backend en cada estado (módulo 4: contratos).
const PUEDE_EDITAR: EstadoContrato[] = ['por_iniciar', 'vigente', 'vencido'];
const EN_CURSO: EstadoContrato[] = ['vigente', 'vencido'];
const PUEDE_TERMINAR: EstadoContrato[] = ['vigente', 'vencido', 'en_terminacion'];

type Accion = 'crear' | 'editar' | 'prorrogar' | 'renovar' | 'terminar' | 'anular';

interface FormularioContrato {
  apartaestudio_id: string;
  residente_id: string;
  fecha_inicio: string;
  fecha_terminacion: string;
  canon_inicial: string;
  porcentaje_incremento: string;
  notas: string;
  fecha_aviso: string;
  fecha_entrega: string;
  motivo: string;
}

const sumarMeses = (fecha: string, meses: number) => {
  const [a, m, d] = fecha.split('-').map(Number);
  const resultado = new Date(Date.UTC(a, m - 1 + meses, d));
  return resultado.toISOString().slice(0, 10);
};

const vacio = (): FormularioContrato => {
  const hoy = obtenerFechaHoyCO();
  return {
    apartaestudio_id: '',
    residente_id: '',
    fecha_inicio: hoy,
    fecha_terminacion: sumarMeses(hoy, 12),
    canon_inicial: '',
    porcentaje_incremento: '',
    notas: '',
    fecha_aviso: hoy,
    fecha_entrega: hoy,
    motivo: '',
  };
};

const TITULOS: Record<Accion, string> = {
  crear: 'Crear Contrato de Arrendamiento',
  editar: 'Editar Contrato',
  prorrogar: 'Prorrogar Contrato',
  renovar: 'Renovar Contrato',
  terminar: 'Registrar Terminación',
  anular: 'Anular Contrato',
};

const SUBTITULOS: Record<Accion, string> = {
  crear: 'Vincula un residente sin bloqueo a un apartaestudio activo y sin ocupación en esas fechas.',
  editar: 'Solo es posible mientras el contrato no tenga cobros generados.',
  prorrogar: 'Amplía la fecha de terminación conservando el mismo contrato y canon.',
  renovar: 'Cierra este contrato y crea uno nuevo enlazado que inicia al día siguiente.',
  terminar: 'Registra el aviso, la entrega del inmueble y el motivo. Puede corregirse hasta la entrega.',
  anular: 'Solo para contratos que aún no han iniciado. Queda registrado en la auditoría.',
};

const NOMBRES_ACCION_HISTORIAL: Record<string, string> = {
  crear: 'Creación',
  editar: 'Edición',
  prorrogar: 'Prórroga',
  renovar: 'Renovación',
  terminar: 'Terminación',
  corregir_terminacion: 'Corrección de terminación',
  anular: 'Anulación',
};

const nombreAccion = (accion: string) => {
  const clave = accion.replace(/^contrato\./, '');
  return NOMBRES_ACCION_HISTORIAL[clave] ?? clave;
};

const claseIcono =
  'p-1.5 rounded transition-colors cursor-pointer text-[#5A5D62] hover:text-[#0B0B0C] dark:text-[#A0A3A8] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5';
const claseFiltro =
  'w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]';

export const PaginaContratos: React.FC = () => {
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [apartaestudios, setApartaestudios] = useState<Apartaestudio[]>([]);
  const [residentes, setResidentes] = useState<Residente[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filtroEstado, setFiltroEstado] = useState<EstadoContrato | ''>('');
  const [filtroApartaestudio, setFiltroApartaestudio] = useState('');
  const [filtroResidente, setFiltroResidente] = useState('');

  const [accion, setAccion] = useState<Accion | null>(null);
  const [seleccionado, setSeleccionado] = useState<Contrato | null>(null);
  const [formulario, setFormulario] = useState<FormularioContrato>(vacio);
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  const [detalle, setDetalle] = useState<ContratoDetalle | null>(null);
  const [historial, setHistorial] = useState<CambioContrato[]>([]);
  const [modalDetalleAbierto, setModalDetalleAbierto] = useState(false);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);

  const { agregarNotificacion, esAdmin } = useAuth();

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [respContratos, respApartas, respResidentes] = await Promise.all([
        listarContratos({
          estado: filtroEstado || undefined,
          apartaestudio_id: filtroApartaestudio ? Number(filtroApartaestudio) : undefined,
          residente_id: filtroResidente ? Number(filtroResidente) : undefined,
        }),
        listarApartaestudios(),
        listarResidentes(),
      ]);
      setContratos(respContratos);
      setApartaestudios(respApartas);
      setResidentes(respResidentes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar contratos');
    } finally {
      setCargando(false);
    }
  }, [filtroEstado, filtroApartaestudio, filtroResidente]);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  const campo = <K extends keyof FormularioContrato>(clave: K, valor: FormularioContrato[K]) =>
    setFormulario((f) => ({ ...f, [clave]: valor }));

  const abrir = (nueva: Accion, c: Contrato | null = null) => {
    const base = vacio();
    if (c) {
      base.fecha_inicio = c.fecha_inicio;
      base.fecha_terminacion =
        nueva === 'prorrogar' || nueva === 'renovar'
          ? sumarMeses(c.fecha_terminacion, 12)
          : c.fecha_terminacion;
      base.canon_inicial = nueva === 'renovar' ? '' : String(Number(c.canon_inicial));
      base.porcentaje_incremento = String(Number(c.porcentaje_incremento));
      base.notas = nueva === 'editar' ? c.notas || '' : '';
      base.fecha_aviso = c.fecha_aviso || base.fecha_aviso;
      base.fecha_entrega = c.fecha_entrega || base.fecha_entrega;
      base.motivo = nueva === 'terminar' ? c.motivo_terminacion || '' : '';
    } else {
      base.apartaestudio_id = String(
        apartaestudios.find((a) => a.activo && estadoApartaestudio(a) === 'libre')?.id ?? ''
      );
    }
    setSeleccionado(c);
    setFormulario(base);
    setErrores({});
    setErrorGeneral(null);
    setAccion(nueva);
  };

  const abrirDetalle = async (c: Contrato) => {
    setSeleccionado(c);
    setDetalle(null);
    setModalDetalleAbierto(true);
    setCargandoDetalle(true);
    try {
      const [d, h] = await Promise.all([obtenerContrato(c.id), obtenerHistorialContrato(c.id)]);
      setDetalle(d);
      setHistorial(h);
    } catch {
      agregarNotificacion('error', 'Error al cargar el historial del contrato');
    } finally {
      setCargandoDetalle(false);
    }
  };

  const validar = (): Record<string, string> => {
    const f = formulario;
    const e: Record<string, string> = {};
    const numero = (v: string) => v.trim() !== '' && !isNaN(Number(v));
    if (accion === 'crear') {
      if (!f.apartaestudio_id) e.apartaestudio_id = 'Selecciona un apartaestudio';
      if (!f.residente_id) e.residente_id = 'Selecciona un residente';
    }
    if (accion === 'crear' || accion === 'editar') {
      if (!f.fecha_inicio) e.fecha_inicio = 'Ingresa la fecha de inicio';
      if (!numero(f.canon_inicial) || Number(f.canon_inicial) <= 0)
        e.canon_inicial = 'Ingresa un canon positivo';
    }
    if (accion === 'crear' || accion === 'editar' || accion === 'renovar') {
      if (!numero(f.porcentaje_incremento) || Number(f.porcentaje_incremento) < 0)
        e.porcentaje_incremento = 'Ingresa un porcentaje (0 o más)';
    }
    if (accion === 'renovar' && f.canon_inicial && !(Number(f.canon_inicial) > 0))
      e.canon_inicial = 'Ingresa un canon positivo o déjalo vacío';
    if (accion && ['crear', 'editar', 'prorrogar', 'renovar'].includes(accion)) {
      if (!f.fecha_terminacion) e.fecha_terminacion = 'Ingresa la fecha de terminación';
      else if ((accion === 'crear' || accion === 'editar') && f.fecha_terminacion <= f.fecha_inicio)
        e.fecha_terminacion = 'Debe ser posterior a la fecha de inicio';
      else if (accion === 'prorrogar' && seleccionado && f.fecha_terminacion <= seleccionado.fecha_terminacion)
        e.fecha_terminacion = 'Debe ser posterior a la terminación actual';
    }
    if (accion === 'terminar') {
      if (!f.fecha_aviso) e.fecha_aviso = 'Ingresa la fecha del aviso';
      if (!f.fecha_entrega) e.fecha_entrega = 'Ingresa la fecha de entrega';
    }
    if ((accion === 'terminar' || accion === 'anular') && f.motivo.trim().length < 3)
      e.motivo = 'Indica el motivo';
    return e;
  };

  const enviar = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!accion) return;
    const e = validar();
    setErrores(e);
    setErrorGeneral(null);
    if (Object.keys(e).length > 0) return;

    const f = formulario;
    const notas = f.notas.trim() || null;
    setGuardando(true);
    try {
      if (accion === 'crear') {
        const nuevo = await crearContrato({
          apartaestudio_id: Number(f.apartaestudio_id),
          residente_id: Number(f.residente_id),
          fecha_inicio: f.fecha_inicio,
          fecha_terminacion: f.fecha_terminacion,
          canon_inicial: f.canon_inicial,
          porcentaje_incremento: f.porcentaje_incremento,
          notas,
        });
        agregarNotificacion('exito', `Contrato #${nuevo.id} creado`);
      } else if (seleccionado) {
        const id = seleccionado.id;
        if (accion === 'editar') {
          const datos: ContratoEditar = {
            fecha_terminacion: f.fecha_terminacion,
            canon_inicial: f.canon_inicial,
            porcentaje_incremento: f.porcentaje_incremento,
            notas,
          };
          // La fecha de inicio solo puede cambiar antes de que el contrato empiece.
          if (seleccionado.estado === 'por_iniciar' && f.fecha_inicio !== seleccionado.fecha_inicio)
            datos.fecha_inicio = f.fecha_inicio;
          await actualizarContrato(id, datos);
          agregarNotificacion('exito', `Contrato #${id} actualizado`);
        } else if (accion === 'prorrogar') {
          await prorrogarContrato(id, f.fecha_terminacion);
          agregarNotificacion('exito', `Contrato #${id} prorrogado`);
        } else if (accion === 'renovar') {
          const nuevo = await renovarContrato(id, {
            fecha_terminacion: f.fecha_terminacion,
            canon_inicial: f.canon_inicial.trim() || null,
            porcentaje_incremento: f.porcentaje_incremento,
            notas,
          });
          agregarNotificacion('exito', `Contrato #${id} renovado como #${nuevo.id}`);
        } else if (accion === 'terminar') {
          await terminarContrato(id, {
            fecha_aviso: f.fecha_aviso,
            fecha_entrega: f.fecha_entrega,
            motivo: f.motivo.trim(),
          });
          agregarNotificacion('info', `Terminación del contrato #${id} registrada`);
        } else if (accion === 'anular') {
          await anularContrato(id, f.motivo.trim());
          agregarNotificacion('info', `Contrato #${id} anulado`);
        }
      }
      setAccion(null);
      cargarDatos();
    } catch (err) {
      if (err instanceof ErrorApi) {
        setErrorGeneral(err.message);
        const mapa: Record<string, string> = {};
        err.detalles.forEach((d) => {
          mapa[d.campo] = d.mensaje;
        });
        setErrores(mapa);
      } else {
        setErrorGeneral('Error inesperado al guardar.');
      }
    } finally {
      setGuardando(false);
    }
  };

  const columnas: Columna<Contrato>[] = [
    {
      clave: 'id',
      encabezado: 'Contrato / Apto',
      render: (c) => (
        <div>
          <span className="font-semibold text-xs text-[#0B0B0C] dark:text-[#FAFAF9]">#{c.id}</span>
          <p className="text-[11px] text-[#8A8D91]">Unidad {c.apartaestudio.codigo}</p>
        </div>
      ),
    },
    {
      clave: 'residente',
      encabezado: 'Residente',
      render: (c) => (
        <div>
          <span className="font-medium text-xs text-[#0B0B0C] dark:text-[#FAFAF9]">
            {c.residente.nombre}
          </span>
          <p className="text-[11px] text-[#8A8D91]">
            {c.residente.tipo_documento} {c.residente.numero_documento}
          </p>
        </div>
      ),
    },
    {
      clave: 'vigencia',
      encabezado: 'Vigencia',
      render: (c) => (
        <span className="text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
          {formatearFechaCO(c.fecha_inicio)} al {formatearFechaCO(c.fecha_terminacion)}
        </span>
      ),
    },
    {
      clave: 'canon',
      encabezado: 'Canon Vigente',
      render: (c) => (
        <div>
          <span className="font-semibold text-xs text-[#0B0B0C] dark:text-[#FAFAF9]">
            {formatearMonedaCOP(c.canon_vigente)}
          </span>
          <p className="text-[10px] text-[#8A8D91]">
            Incremento anual {Number(c.porcentaje_incremento)} %
          </p>
        </div>
      ),
    },
    {
      clave: 'estado',
      encabezado: 'Estado',
      render: (c) => <InsigniaEstado tipo="contrato" valor={c.estado} tamano="sm" />,
    },
    {
      clave: 'acciones',
      encabezado: 'Acciones',
      alineacion: 'derecha',
      render: (c) => {
        const renovado = c.contrato_siguiente_id !== null;
        return (
          <div className="flex items-center justify-end gap-1">
            <button onClick={() => abrirDetalle(c)} title="Detalle e historial" className={claseIcono}>
              <History className="w-4 h-4" />
            </button>
            {PUEDE_EDITAR.includes(c.estado) && !renovado && (
              <button onClick={() => abrir('editar', c)} title="Editar contrato" className={claseIcono}>
                <Edit2 className="w-4 h-4" />
              </button>
            )}
            {EN_CURSO.includes(c.estado) && !renovado && (
              <>
                <button onClick={() => abrir('prorrogar', c)} title="Prorrogar" className={claseIcono}>
                  <CalendarPlus className="w-4 h-4" />
                </button>
                <button onClick={() => abrir('renovar', c)} title="Renovar" className={claseIcono}>
                  <RotateCw className="w-4 h-4" />
                </button>
              </>
            )}
            {PUEDE_TERMINAR.includes(c.estado) && !renovado && (
              <button
                onClick={() => abrir('terminar', c)}
                title={c.estado === 'en_terminacion' ? 'Corregir terminación' : 'Registrar terminación'}
                className="p-1.5 text-[#805B10] hover:bg-[#805B10]/10 rounded transition-colors cursor-pointer"
              >
                <XCircle className="w-4 h-4" />
              </button>
            )}
            {esAdmin && c.estado === 'por_iniciar' && c.contrato_anterior_id === null && (
              <button
                onClick={() => abrir('anular', c)}
                title="Anular contrato"
                className="p-1.5 text-[#7A1F2B] hover:bg-[#7A1F2B]/10 rounded transition-colors cursor-pointer"
              >
                <Ban className="w-4 h-4" />
              </button>
            )}
          </div>
        );
      },
    },
  ];

  const muestra = (claves: Accion[]) => accion !== null && claves.includes(accion);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-[#E3E4E6] dark:border-[#2A2A2E]">
        <div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-[#8A8D91]">
            Gestión Contractual
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
            Contratos de Arrendamiento
          </h1>
        </div>
        <Boton variante="plata" onClick={() => abrir('crear')} icono={<Plus className="w-4 h-4" />}>
          Crear Nuevo Contrato
        </Boton>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-white dark:bg-[#141416] p-4 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
        <select
          value={filtroEstado}
          onChange={(e) => setFiltroEstado(e.target.value as EstadoContrato | '')}
          className={claseFiltro}
          aria-label="Filtrar por estado"
        >
          <option value="">Todos los estados</option>
          {ESTADOS_CONTRATO.map((e) => (
            <option key={e} value={e}>
              {NOMBRES_ESTADO_CONTRATO[e]}
            </option>
          ))}
        </select>
        <select
          value={filtroApartaestudio}
          onChange={(e) => setFiltroApartaestudio(e.target.value)}
          className={claseFiltro}
          aria-label="Filtrar por apartaestudio"
        >
          <option value="">Todos los apartaestudios</option>
          {apartaestudios.map((a) => (
            <option key={a.id} value={a.id}>
              Apto {a.codigo}
            </option>
          ))}
        </select>
        <select
          value={filtroResidente}
          onChange={(e) => setFiltroResidente(e.target.value)}
          className={claseFiltro}
          aria-label="Filtrar por residente"
        >
          <option value="">Todos los residentes</option>
          {residentes.map((r) => (
            <option key={r.id} value={r.id}>
              {r.nombre}
            </option>
          ))}
        </select>
      </div>

      <Tabla
        columnas={columnas}
        datos={contratos}
        cargando={cargando}
        error={error}
        alReintentar={cargarDatos}
        mensajeVacio="No hay contratos con los filtros indicados"
        subtituloVacio="Crea un contrato vinculando un residente y un apartaestudio libre."
      />

      {/* Un solo modal para todas las acciones del ciclo de vida */}
      <Modal
        abierto={accion !== null}
        alCerrar={() => setAccion(null)}
        titulo={
          accion
            ? `${TITULOS[accion]}${seleccionado && accion !== 'crear' ? ` #${seleccionado.id}` : ''}`
            : ''
        }
        subtitulo={accion ? SUBTITULOS[accion] : undefined}
        tamano={accion === 'crear' ? 'lg' : 'md'}
      >
        <form onSubmit={enviar} className="space-y-4">
          {errorGeneral && (
            <div className="p-4 bg-[#FCF4F5] dark:bg-[#251013] border border-[#7A1F2B]/40 rounded-[4px] flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-[#7A1F2B] dark:text-[#EFA3AC] shrink-0 mt-0.5" />
              <div className="text-xs text-[#7A1F2B] dark:text-[#EFA3AC] leading-relaxed">
                <span className="font-semibold block uppercase tracking-wide">
                  Validación del servidor
                </span>
                {errorGeneral}
              </div>
            </div>
          )}

          {muestra(['crear']) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Campo label="Apartaestudio" obligatorio error={errores.apartaestudio_id} id="c_aparta">
                <EntradaSeleccion
                  id="c_aparta"
                  value={formulario.apartaestudio_id}
                  onChange={(e) => campo('apartaestudio_id', e.target.value)}
                  tieneError={Boolean(errores.apartaestudio_id)}
                >
                  <option value="">Selecciona una unidad</option>
                  {apartaestudios
                    .filter((a) => a.activo)
                    .map((a) => (
                      <option key={a.id} value={a.id}>
                        Apto {a.codigo} — {estadoApartaestudio(a)}
                      </option>
                    ))}
                </EntradaSeleccion>
              </Campo>
              <Campo label="Residente" obligatorio error={errores.residente_id} id="c_residente">
                <EntradaSeleccion
                  id="c_residente"
                  value={formulario.residente_id}
                  onChange={(e) => campo('residente_id', e.target.value)}
                  tieneError={Boolean(errores.residente_id)}
                >
                  <option value="">Selecciona un residente</option>
                  {residentes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.nombre} ({r.tipo_documento} {r.numero_documento})
                    </option>
                  ))}
                </EntradaSeleccion>
              </Campo>
            </div>
          )}

          {muestra(['crear', 'editar', 'prorrogar', 'renovar']) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {muestra(['crear', 'editar']) && (
                <Campo
                  label="Fecha de inicio"
                  obligatorio
                  error={errores.fecha_inicio}
                  ayuda={
                    accion === 'editar' && seleccionado?.estado !== 'por_iniciar'
                      ? 'No se puede cambiar: el contrato ya inició'
                      : undefined
                  }
                  id="c_inicio"
                >
                  <EntradaTexto
                    id="c_inicio"
                    type="date"
                    value={formulario.fecha_inicio}
                    disabled={accion === 'editar' && seleccionado?.estado !== 'por_iniciar'}
                    onChange={(e) => campo('fecha_inicio', e.target.value)}
                    tieneError={Boolean(errores.fecha_inicio)}
                  />
                </Campo>
              )}
              <Campo
                label={accion === 'prorrogar' ? 'Nueva fecha de terminación' : 'Fecha de terminación'}
                obligatorio
                error={errores.fecha_terminacion}
                ayuda={
                  seleccionado && muestra(['prorrogar', 'renovar'])
                    ? `Terminación actual: ${formatearFechaCO(seleccionado.fecha_terminacion)}`
                    : undefined
                }
                id="c_fin"
              >
                <EntradaTexto
                  id="c_fin"
                  type="date"
                  value={formulario.fecha_terminacion}
                  onChange={(e) => campo('fecha_terminacion', e.target.value)}
                  tieneError={Boolean(errores.fecha_terminacion)}
                />
              </Campo>
            </div>
          )}

          {muestra(['crear', 'editar', 'renovar']) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Campo
                label="Canon inicial (COP)"
                obligatorio={accion !== 'renovar'}
                error={errores.canon_inicial}
                ayuda={
                  accion === 'renovar' && seleccionado
                    ? `Vacío = canon vigente con incremento (${formatearMonedaCOP(seleccionado.canon_vigente)} hoy)`
                    : undefined
                }
                id="c_canon"
              >
                <EntradaTexto
                  id="c_canon"
                  type="number"
                  min="0"
                  step="1000"
                  value={formulario.canon_inicial}
                  onChange={(e) => campo('canon_inicial', e.target.value)}
                  tieneError={Boolean(errores.canon_inicial)}
                />
              </Campo>
              <Campo
                label="Incremento anual (%)"
                obligatorio
                error={errores.porcentaje_incremento}
                id="c_incremento"
              >
                <EntradaTexto
                  id="c_incremento"
                  type="number"
                  min="0"
                  step="0.01"
                  value={formulario.porcentaje_incremento}
                  onChange={(e) => campo('porcentaje_incremento', e.target.value)}
                  tieneError={Boolean(errores.porcentaje_incremento)}
                />
              </Campo>
            </div>
          )}

          {muestra(['crear', 'editar', 'renovar']) && (
            <Campo label="Notas" error={errores.notas} id="c_notas">
              <EntradaAreaTexto
                id="c_notas"
                rows={3}
                value={formulario.notas}
                onChange={(e) => campo('notas', e.target.value)}
              />
            </Campo>
          )}

          {muestra(['terminar']) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Campo label="Fecha del aviso" obligatorio error={errores.fecha_aviso} id="c_aviso">
                <EntradaTexto
                  id="c_aviso"
                  type="date"
                  max={obtenerFechaHoyCO()}
                  value={formulario.fecha_aviso}
                  onChange={(e) => campo('fecha_aviso', e.target.value)}
                  tieneError={Boolean(errores.fecha_aviso)}
                />
              </Campo>
              <Campo label="Fecha de entrega" obligatorio error={errores.fecha_entrega} id="c_entrega">
                <EntradaTexto
                  id="c_entrega"
                  type="date"
                  value={formulario.fecha_entrega}
                  onChange={(e) => campo('fecha_entrega', e.target.value)}
                  tieneError={Boolean(errores.fecha_entrega)}
                />
              </Campo>
            </div>
          )}

          {muestra(['terminar', 'anular']) && (
            <Campo label="Motivo" obligatorio error={errores.motivo} id="c_motivo">
              <EntradaAreaTexto
                id="c_motivo"
                rows={3}
                value={formulario.motivo}
                onChange={(e) => campo('motivo', e.target.value)}
              />
            </Campo>
          )}

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-[#E3E4E6] dark:border-[#2A2A2E]">
            <Boton type="button" variante="fantasma" onClick={() => setAccion(null)} disabled={guardando}>
              Cancelar
            </Boton>
            <Boton
              type="submit"
              variante={accion === 'anular' ? 'peligro' : 'plata'}
              cargando={guardando}
            >
              {accion === 'crear' ? 'Crear Contrato' : 'Confirmar'}
            </Boton>
          </div>
        </form>
      </Modal>

      {/* Detalle con línea de tiempo del historial */}
      <Modal
        abierto={modalDetalleAbierto}
        alCerrar={() => setModalDetalleAbierto(false)}
        titulo={`Expediente del Contrato #${seleccionado?.id ?? ''}`}
        subtitulo="Condiciones vigentes, prórrogas y cambios registrados con su autor."
        tamano="lg"
      >
        {cargandoDetalle ? (
          <div className="py-12 text-center text-xs text-[#8A8D91] uppercase tracking-wider">
            Cargando historial...
          </div>
        ) : detalle ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-[#FAFAF9] dark:bg-[#1A1A1D] p-4 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
              <Dato titulo="Inmueble">
                Apartaestudio {detalle.apartaestudio.codigo}
                <Sub>Canon vigente: {formatearMonedaCOP(detalle.canon_vigente)}</Sub>
                <Sub>Canon inicial: {formatearMonedaCOP(detalle.canon_inicial)}</Sub>
              </Dato>
              <Dato titulo="Residente">
                {detalle.residente.nombre}
                <Sub>
                  {detalle.residente.tipo_documento} {detalle.residente.numero_documento}
                </Sub>
              </Dato>
              <Dato titulo="Estado">
                <InsigniaEstado tipo="contrato" valor={detalle.estado} tamano="md" />
              </Dato>
              <Dato titulo="Vigencia">
                {formatearFechaCO(detalle.fecha_inicio)} al {formatearFechaCO(detalle.fecha_terminacion)}
                <Sub>Día de corte: {detalle.dia_corte}</Sub>
              </Dato>
              <Dato titulo="Próximo corte">
                {formatearFechaCO(detalle.proximo_corte)}
                <Sub>Próximo aniversario: {formatearFechaCO(detalle.proximo_aniversario)}</Sub>
              </Dato>
              <Dato titulo="Creado">
                {formatearFechaHoraCO(detalle.creado_en)}
                <Sub>Por {detalle.creado_por.nombre}</Sub>
              </Dato>
              {(detalle.fecha_entrega || detalle.motivo_anulacion) && (
                <div className="sm:col-span-3 pt-2 border-t border-[#E3E4E6] dark:border-[#2A2A2E] text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
                  {detalle.fecha_entrega && (
                    <p>
                      Aviso {formatearFechaCO(detalle.fecha_aviso)} · Entrega{' '}
                      {formatearFechaCO(detalle.fecha_entrega)} · Motivo: {detalle.motivo_terminacion}
                    </p>
                  )}
                  {detalle.motivo_anulacion && <p>Anulado: {detalle.motivo_anulacion}</p>}
                </div>
              )}
              {detalle.notas && (
                <div className="sm:col-span-3 pt-2 border-t border-[#E3E4E6] dark:border-[#2A2A2E] text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
                  Notas: {detalle.notas}
                </div>
              )}
            </div>

            {detalle.prorrogas.length > 0 && (
              <div className="text-xs text-[#5A5D62] dark:text-[#A0A3A8] space-y-1">
                <h4 className="font-serif-luxury text-base font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mb-2">
                  Prórrogas
                </h4>
                {detalle.prorrogas.map((p) => (
                  <p key={p.id}>
                    {formatearFechaCO(p.terminacion_anterior)} → {formatearFechaCO(p.terminacion_nueva)} ·{' '}
                    {p.registrada_por.nombre}, {formatearFechaHoraCO(p.registrada_en)}
                  </p>
                ))}
              </div>
            )}

            <div>
              <h4 className="font-serif-luxury text-base font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mb-4 flex items-center gap-2">
                <History className="w-4 h-4 text-[#8A8D91]" />
                Línea de Tiempo del Historial
              </h4>
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#E3E4E6] dark:before:bg-[#2A2A2E]">
                {historial.map((h, i) => (
                  <div key={i} className="relative">
                    <div className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-[#111113] border-2 border-[#C0C0C0]" />
                    <div className="bg-white dark:bg-[#141416] p-3.5 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold uppercase tracking-wider text-[#0B0B0C] dark:text-[#FAFAF9]">
                          {nombreAccion(h.accion)}
                        </span>
                        <span className="text-[11px] text-[#8A8D91]">{formatearFechaHoraCO(h.momento)}</span>
                      </div>
                      {h.valor_nuevo && (
                        <p className="text-[11px] font-mono text-[#5A5D62] dark:text-[#A0A3A8] mt-1 break-all">
                          {Object.entries(h.valor_nuevo)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(' · ')}
                        </p>
                      )}
                      <p className="text-[10px] text-[#8A8D91] mt-1.5 flex items-center gap-1">
                        <User className="w-3 h-3" /> {h.usuario?.nombre ?? 'Sistema'}
                      </p>
                    </div>
                  </div>
                ))}
                {historial.length === 0 && (
                  <div className="text-xs text-[#8A8D91] py-2">No hay eventos registrados.</div>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Boton variante="secundario" tamano="sm" onClick={() => setModalDetalleAbierto(false)}>
                Cerrar
              </Boton>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
};

const Dato: React.FC<{ titulo: string; children: React.ReactNode }> = ({ titulo, children }) => (
  <div>
    <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">{titulo}</p>
    <div className="text-sm font-semibold text-[#0B0B0C] dark:text-[#FAFAF9] mt-0.5">{children}</div>
  </div>
);

const Sub: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <p className="text-xs font-normal text-[#8A8D91]">{children}</p>
);
