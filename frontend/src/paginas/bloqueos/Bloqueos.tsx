import React, { useEffect, useState, useCallback } from 'react';
import {
  listarBloqueos,
  crearBloqueo,
  levantarBloqueo,
  verificarBloqueo,
} from '../../api/bloqueos';
import { Bloqueo, BloqueoCrear, TipoDocumento, VerificarBloqueoRespuesta, EstadoBloqueo
 } from '../../api/tipos';
import { OpcionesDocumento } from '../../componentes/OpcionesDocumento';
import { Tabla, Columna } from '../../componentes/Tabla';
import { Boton } from '../../componentes/Boton';
import { Modal } from '../../componentes/Modal';
import { Campo, EntradaTexto, EntradaSeleccion, EntradaAreaTexto } from '../../componentes/Campo';
import { InsigniaEstado } from '../../componentes/InsigniaEstado';
import { useAuth } from '../../contexto/AuthContext';
import { puede } from '../../utilidades/permisos';
import { ErrorApi } from '../../api/cliente';
import { formatearFechaHoraCO } from '../../utilidades/formato';
import {
  ShieldAlert,
  ShieldCheck,
  Search,
  Plus,
  Unlock,
  CheckCircle2,
  AlertCircle,
  FileSearch,
} from 'lucide-react';

export const PaginaBloqueos: React.FC = () => {
  const [bloqueos, setBloqueos] = useState<Bloqueo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [busqueda, setBusqueda] = useState('');
  const [filtroActivo, setFiltroActivo] = useState<EstadoBloqueo>('activos');

  // Modal Bloquear
  const [modalBloquearAbierto, setModalBloquearAbierto] = useState(false);
  const [guardandoBloqueo, setGuardandoBloqueo] = useState(false);
  const [formularioBloqueo, setFormularioBloqueo] = useState<BloqueoCrear>({
    tipo_documento: 'CC',
    numero_documento: '',
    nombre: '',
    motivo: '',
  });
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});

  // Modal Levantar Bloqueo
  const [modalLevantarAbierto, setModalLevantarAbierto] = useState(false);
  const [bloqueoALevantar, setBloqueoALevantar] = useState<Bloqueo | null>(null);
  const [motivoLevantamiento, setMotivoLevantamiento] = useState('');
  const [errorLevantamiento, setErrorLevantamiento] = useState<string | null>(null);
  const [levantando, setLevantando] = useState(false);

  // Herramienta "Verificar documento"
  const [tipoDocVerificar, setTipoDocVerificar] = useState<TipoDocumento>('CC');
  const [numDocVerificar, setNumDocVerificar] = useState('');
  const [verificando, setVerificando] = useState(false);
  const [resultadoVerificacion, setResultadoVerificacion] = useState<VerificarBloqueoRespuesta | null>(
    null
  );

  const { agregarNotificacion, usuario } = useAuth();
  const puedeGestionar = puede(usuario, 'gestionar_bloqueos');

  const cargarBloqueos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await listarBloqueos({
        texto: busqueda.trim() || undefined,
        estado: filtroActivo,
      });
      setBloqueos(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar bloqueos';
      setError(msg);
    } finally {
      setCargando(false);
    }
  }, [busqueda, filtroActivo]);

  useEffect(() => {
    cargarBloqueos();
  }, [cargarBloqueos]);

  const abrirModalBloquear = () => {
    setFormularioBloqueo({
      tipo_documento: 'CC',
      numero_documento: '',
      nombre: '',
      motivo: '',
    });
    setErroresCampos({});
    setModalBloquearAbierto(true);
  };

  const abrirModalLevantar = (b: Bloqueo) => {
    setBloqueoALevantar(b);
    setMotivoLevantamiento('');
    setErrorLevantamiento(null);
    setModalLevantarAbierto(true);
  };

  const manejarGuardarBloqueo = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroresCampos({});

    const errs: Record<string, string> = {};
    if (!formularioBloqueo.numero_documento.trim()) {
      errs.numero_documento = 'El número de documento es obligatorio';
    }
    if (!formularioBloqueo.nombre.trim()) {
      errs.nombre = 'El nombre completo es obligatorio';
    }
    if (!formularioBloqueo.motivo.trim() || formularioBloqueo.motivo.trim().length < 10) {
      errs.motivo = 'El motivo es obligatorio y debe tener al menos 10 caracteres';
    }

    if (Object.keys(errs).length > 0) {
      setErroresCampos(errs);
      return;
    }

    setGuardandoBloqueo(true);
    try {
      await crearBloqueo(formularioBloqueo);
      agregarNotificacion('error', `Bloqueo registrado para ${formularioBloqueo.nombre}`);
      setModalBloquearAbierto(false);
      cargarBloqueos();
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
      setGuardandoBloqueo(false);
    }
  };

  const manejarLevantarBloqueo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bloqueoALevantar) return;
    if (!motivoLevantamiento.trim() || motivoLevantamiento.trim().length < 5) {
      setErrorLevantamiento('Indica un motivo de levantamiento de al menos 5 caracteres');
      return;
    }

    setLevantando(true);
    try {
      await levantarBloqueo(bloqueoALevantar.id, motivoLevantamiento.trim());
      agregarNotificacion('exito', `Bloqueo levantado para ${bloqueoALevantar.nombre}`);
      setModalLevantarAbierto(false);
      cargarBloqueos();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al levantar el bloqueo';
      setErrorLevantamiento(msg);
    } finally {
      setLevantando(false);
    }
  };

  const ejecutarVerificacion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!numDocVerificar.trim()) return;

    setVerificando(true);
    setResultadoVerificacion(null);
    try {
      const resp = await verificarBloqueo(tipoDocVerificar, numDocVerificar.trim());
      setResultadoVerificacion(resp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al verificar documento';
      agregarNotificacion('error', msg);
    } finally {
      setVerificando(false);
    }
  };

  const columnas: Columna<Bloqueo>[] = [
    {
      clave: 'documento',
      encabezado: 'Documento',
      render: (b) => (
        <span className="font-semibold text-xs text-tinta">
          {b.tipo_documento} {b.numero_documento}
        </span>
      ),
    },
    {
      clave: 'nombre',
      encabezado: 'Persona Bloqueada',
      render: (b) => (
        <div>
          <span className="font-medium text-sm text-tinta">
            {b.nombre}
          </span>
          <p className="text-[11px] text-tenue">
            Registrado por: {b.bloqueado_por.nombre} · {formatearFechaHoraCO(b.bloqueado_en)}
          </p>
        </div>
      ),
    },
    {
      clave: 'motivo',
      encabezado: 'Motivo del Bloqueo',
      render: (b) => (
        <div className="max-w-xs">
          <p className="text-xs text-tinta-2 line-clamp-2" title={b.motivo ?? undefined}>
            {b.motivo ?? 'Reservado para administradores'}
          </p>
          {b.motivo_levantamiento && (
            <p className="text-[10px] text-exito mt-1 italic">
              Levantamiento: {b.motivo_levantamiento} ({b.levantado_por?.nombre})
            </p>
          )}
        </div>
      ),
    },
    {
      clave: 'estado',
      encabezado: 'Estado',
      render: (b) => (
        <InsigniaEstado
          tipo="bloqueo"
          valor={b.activo}
          tamano="sm"
        />
      ),
    },
    {
      clave: 'acciones',
      encabezado: 'Acciones',
      alineacion: 'derecha',
      render: (b) => (
        <div className="flex items-center justify-end">
          {b.activo && puedeGestionar ? (
            <Boton
              tamano="sm"
              variante="secundario"
              onClick={() => abrirModalLevantar(b)}
              icono={<Unlock className="w-3.5 h-3.5" />}
            >
              Levantar Bloqueo
            </Boton>
          ) : b.activo ? (
            <span className="text-[11px] text-tenue italic">Activo</span>
          ) : (
            <span className="text-[11px] text-tenue italic">Levantado</span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-linea">
        <div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-tenue">
            Control de Seguridad & Restricciones
          </span>
          <h1 className="text-2xl sm:text-3xl font-titulo font-medium text-tinta mt-1">
            Bloqueos de Personas
          </h1>
        </div>
        {puedeGestionar && (
          <Boton
            variante="peligro"
            onClick={abrirModalBloquear}
            icono={<ShieldAlert className="w-4 h-4" />}
          >
            Bloquear Persona
          </Boton>
        )}
      </div>

      {/* Herramienta obligatoria: Verificar Documento (GET /bloqueos/verificar) */}
      <div className="bg-panel p-6 rounded-lg border border-linea-fuerte shadow-xs">
        <div className="flex items-center gap-2 mb-3">
          <FileSearch className="w-5 h-5 text-tenue" />
          <h2 className="text-base font-titulo font-medium text-tinta">
            Herramienta: Verificar Documento en Base de Restricciones
          </h2>
        </div>
        <p className="text-xs text-tinta-2 mb-4">
          Consulta al instante si un arrendatario o postulante tiene restricciones activas que le
          impidan firmar contratos.
        </p>

        <form onSubmit={ejecutarVerificacion} className="flex flex-col sm:flex-row gap-3">
          <div className="w-full sm:w-44">
            <EntradaSeleccion
              value={tipoDocVerificar}
              onChange={(e) => setTipoDocVerificar(e.target.value as TipoDocumento)}
            >
              <OpcionesDocumento />
            </EntradaSeleccion>
          </div>

          <div className="flex-1">
            <EntradaTexto
              type="text"
              placeholder="Ingresa el número de documento a verificar..."
              value={numDocVerificar}
              onChange={(e) => setNumDocVerificar(e.target.value)}
            />
          </div>

          <Boton
            type="submit"
            variante="plata"
            cargando={verificando}
            icono={<Search className="w-4 h-4" />}
          >
            Verificar Estado
          </Boton>
        </form>

        {/* Resultado de verificación */}
        {resultadoVerificacion !== null && (
          <div className="mt-4 pt-4 border-t border-linea">
            {resultadoVerificacion.bloqueado ? (
              <div className="p-4 bg-peligro-bg border border-peligro/40 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-peligro shrink-0 mt-0.5" />
                <div className="text-xs text-peligro">
                  <span className="font-semibold text-sm block">
                    PERSONA BLOQUEADA: No se permite emitir contratos
                  </span>
                  <p className="mt-0.5 text-[11px] opacity-80">
                    Bloqueado desde: {formatearFechaHoraCO(resultadoVerificacion.desde)}
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-exito-bg border border-exito/40 rounded-lg flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-exito shrink-0" />
                <div className="text-xs text-exito">
                  <span className="font-semibold text-sm block">
                    Documento Habilitado
                  </span>
                  No registra ningún bloqueo administrativo vigente en el sistema.
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Filtros de la tabla */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-panel p-3 rounded-lg border border-linea">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-tenue absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por cédula o nombre en la lista..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-transparent border-0 outline-none text-tinta"
          />
        </div>

        <div className="w-full sm:w-44">
          <select
            value={filtroActivo}
            onChange={(e) => setFiltroActivo(e.target.value as EstadoBloqueo)}
            className="w-full px-3 py-1.5 text-xs bg-transparent border border-linea-fuerte rounded-lg text-tinta"
          >
            <option value="todos">Todos los registros</option>
            <option value="activos">Solo Bloqueos Activos</option>
            <option value="levantados">Solo Levantados</option>
          </select>
        </div>
      </div>

      {/* Tabla de bloqueos */}
      <Tabla
        columnas={columnas}
        datos={bloqueos}
        cargando={cargando}
        error={error}
        alReintentar={cargarBloqueos}
        mensajeVacio="No hay registros de personas bloqueadas"
        subtituloVacio="Todas las personas están autorizadas para celebrar contratos de arrendamiento."
      />

      {/* Modal Bloquear Persona */}
      <Modal
        abierto={modalBloquearAbierto}
        alCerrar={() => setModalBloquearAbierto(false)}
        titulo="Registrar Bloqueo de Persona"
        subtitulo="Esta acción restringirá inmediatamente la creación o renovación de contratos para este documento."
        tamano="md"
      >
        <form onSubmit={manejarGuardarBloqueo} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Campo label="Tipo Doc" obligatorio error={erroresCampos.tipo_documento} id="tipo_doc_bloq">
              <EntradaSeleccion
                id="tipo_doc_bloq"
                value={formularioBloqueo.tipo_documento}
                onChange={(e) =>
                  setFormularioBloqueo({
                    ...formularioBloqueo,
                    tipo_documento: e.target.value as TipoDocumento,
                  })
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
                id="num_doc_bloq"
              >
                <EntradaTexto
                  id="num_doc_bloq"
                  placeholder="ej. 10203040"
                  value={formularioBloqueo.numero_documento}
                  onChange={(e) =>
                    setFormularioBloqueo({
                      ...formularioBloqueo,
                      numero_documento: e.target.value,
                    })
                  }
                  tieneError={Boolean(erroresCampos.numero_documento)}
                />
              </Campo>
            </div>
          </div>

          <Campo
            label="Nombre Completo"
            obligatorio
            error={erroresCampos.nombre}
            id="nom_bloq"
          >
            <EntradaTexto
              id="nom_bloq"
              placeholder="ej. Andrés Felipe Salazar"
              value={formularioBloqueo.nombre}
              onChange={(e) =>
                setFormularioBloqueo({
                  ...formularioBloqueo,
                  nombre: e.target.value,
                })
              }
              tieneError={Boolean(erroresCampos.nombre)}
            />
          </Campo>

          <Campo
            label="Motivo del Bloqueo (Obligatorio)"
            obligatorio
            ayuda="Mínimo 10 caracteres"
            error={erroresCampos.motivo}
            id="motivo_bloq"
          >
            <EntradaAreaTexto
              id="motivo_bloq"
              placeholder="Detalla la causal: incumplimiento reiterado de canon, daños a la propiedad, problemas de convivencia, etc."
              rows={4}
              value={formularioBloqueo.motivo}
              onChange={(e) =>
                setFormularioBloqueo({
                  ...formularioBloqueo,
                  motivo: e.target.value,
                })
              }
              tieneError={Boolean(erroresCampos.motivo)}
            />
          </Campo>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-linea">
            <Boton
              type="button"
              variante="fantasma"
              onClick={() => setModalBloquearAbierto(false)}
              disabled={guardandoBloqueo}
            >
              Cancelar
            </Boton>
            <Boton type="submit" variante="peligro" cargando={guardandoBloqueo}>
              Confirmar Bloqueo
            </Boton>
          </div>
        </form>
      </Modal>

      {/* Modal Levantar Bloqueo */}
      <Modal
        abierto={modalLevantarAbierto}
        alCerrar={() => setModalLevantarAbierto(false)}
        titulo={`Levantar Bloqueo · ${bloqueoALevantar?.nombre}`}
        subtitulo="Restablecerá los permisos para celebrar contratos de arrendamiento con esta persona."
        tamano="sm"
      >
        <form onSubmit={manejarLevantarBloqueo} className="space-y-4">
          {errorLevantamiento && (
            <div className="p-3 bg-peligro-bg border border-peligro/40 rounded text-xs text-peligro">
              {errorLevantamiento}
            </div>
          )}

          <div className="p-3 bg-fondo rounded border border-linea text-xs space-y-1">
            <span className="text-tenue block uppercase tracking-wider text-[10px]">
              Motivo de Bloqueo Original
            </span>
            <p className="text-tinta">{bloqueoALevantar?.motivo}</p>
          </div>

          <Campo
            label="Motivo del Levantamiento"
            obligatorio
            ayuda="Mínimo 5 caracteres"
            id="motivo_levantar"
          >
            <EntradaAreaTexto
              id="motivo_levantar"
              placeholder="ej. Se subsanaron los saldos pendientes y se firmó acuerdo de conciliación."
              rows={3}
              value={motivoLevantamiento}
              onChange={(e) => setMotivoLevantamiento(e.target.value)}
              disabled={levantando}
            />
          </Campo>

          <div className="pt-3 flex items-center justify-end gap-2 border-t border-linea">
            <Boton
              type="button"
              variante="fantasma"
              onClick={() => setModalLevantarAbierto(false)}
              disabled={levantando}
            >
              Cancelar
            </Boton>
            <Boton
              type="submit"
              variante="plata"
              cargando={levantando}
              icono={<Unlock className="w-4 h-4" />}
            >
              Levantar Bloqueo
            </Boton>
          </div>
        </form>
      </Modal>
    </div>
  );
};
