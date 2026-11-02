import React, { useEffect, useState, useCallback } from 'react';
import { listarAuditoria } from '../../api/auditoria';
import { listarUsuarios } from '../../api/usuarios';
import { RegistroAuditoria, Usuario } from '../../api/tipos';
import { Tabla, Columna } from '../../componentes/Tabla';
import { Boton } from '../../componentes/Boton';
import { Modal } from '../../componentes/Modal';
import { formatearFechaHoraCO } from '../../utilidades/formato';
import {
  History,
  Search,
  Filter,
  Eye,
  RefreshCw,
  Shield,
  FileCode,
} from 'lucide-react';

export const PaginaAuditoria: React.FC = () => {
  const [registros, setRegistros] = useState<RegistroAuditoria[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);

  // Filtros solicitados: usuario, accion, modulo, fecha_desde, fecha_hasta
  const [filtroUsuario, setFiltroUsuario] = useState('');
  const [filtroAccion, setFiltroAccion] = useState('');
  const [filtroModulo, setFiltroModulo] = useState('');
  const [filtroFechaDesde, setFiltroFechaDesde] = useState('');
  const [filtroFechaHasta, setFiltroFechaHasta] = useState('');

  // Modal Detalle
  const [registroSeleccionado, setRegistroSeleccionado] = useState<RegistroAuditoria | null>(null);

  const cargarAuditoria = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const pagina = await listarAuditoria({
        usuario_id: filtroUsuario ? Number(filtroUsuario) : undefined,
        accion: filtroAccion.trim() || undefined,
        entidad: filtroModulo || undefined,
        desde: filtroFechaDesde || undefined,
        hasta: filtroFechaHasta || undefined,
        limite: 200,
      });
      setRegistros(pagina.registros);
      setTotal(pagina.total);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar registros de auditoría';
      setError(msg);
    } finally {
      setCargando(false);
    }
  }, [filtroUsuario, filtroAccion, filtroModulo, filtroFechaDesde, filtroFechaHasta]);

  useEffect(() => {
    cargarAuditoria();
  }, [cargarAuditoria]);

  useEffect(() => {
    listarUsuarios().then(setUsuarios).catch(() => setUsuarios([]));
  }, []);

  const nombreUsuario = (id: number | null) =>
    id === null ? 'Sistema' : usuarios.find((u) => u.id === id)?.nombre ?? `Usuario #${id}`;

  const limpiarFiltros = () => {
    setFiltroUsuario('');
    setFiltroAccion('');
    setFiltroModulo('');
    setFiltroFechaDesde('');
    setFiltroFechaHasta('');
  };

  const columnas: Columna<RegistroAuditoria>[] = [
    {
      clave: 'momento',
      encabezado: 'Fecha y Hora (Bogotá)',
      render: (r) => (
        <span className="text-xs font-mono text-tinta">
          {formatearFechaHoraCO(r.momento)}
        </span>
      ),
    },
    {
      clave: 'usuario',
      encabezado: 'Usuario',
      render: (r) => (
        <div>
          <span className="font-semibold text-xs text-tinta">
            {nombreUsuario(r.usuario_id)}
          </span>
        </div>
      ),
    },
    {
      clave: 'modulo',
      encabezado: 'Entidad',
      render: (r) => (
        <span className="text-xs font-medium px-2 py-0.5 rounded bg-sutil text-tinta border border-linea uppercase">
          {r.entidad}
        </span>
      ),
    },
    {
      clave: 'accion',
      encabezado: 'Acción Ejecutada',
      render: (r) => (
        <span className="text-xs font-semibold uppercase tracking-wider text-tinta">
          {r.accion}
        </span>
      ),
    },
    {
      clave: 'entidad_id',
      encabezado: 'Registro',
      render: (r) => (
        <span className="text-xs font-mono text-tinta-2">
          {r.entidad_id ? `#${r.entidad_id}` : '—'}
        </span>
      ),
    },
    {
      clave: 'ip',
      encabezado: 'IP Origen',
      render: (r) => (
        <span className="text-[11px] font-mono text-tenue">
          {r.ip || '—'}
        </span>
      ),
    },
    {
      clave: 'acciones',
      encabezado: 'Detalle',
      alineacion: 'derecha',
      render: (r) => (
        <button
          onClick={() => setRegistroSeleccionado(r)}
          title="Ver carga técnica (JSON)"
          className="p-1.5 text-tinta-2 hover:text-tinta rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
        >
          <Eye className="w-4 h-4" />
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-linea">
        <div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-tenue">
            Trazabilidad & Cumplimiento (Solo Administrador)
          </span>
          <h1 className="text-2xl sm:text-3xl font-titulo font-medium text-tinta mt-1">
            Registro de Auditoría
          </h1>
        </div>
        <Boton
          variante="secundario"
          tamano="sm"
          onClick={cargarAuditoria}
          cargando={cargando}
          icono={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refrescar Bitácora
        </Boton>
      </div>

      {/* Formulario de Filtros */}
      <div className="bg-panel p-4 rounded-lg border border-linea space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-linea">
          <span className="text-[10px] font-semibold tracking-widest uppercase text-tenue flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5" /> Filtros de Auditoría
          </span>
          <button
            onClick={limpiarFiltros}
            className="text-xs text-tenue hover:text-tinta"
          >
            Limpiar filtros
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-tenue block mb-1">
              Usuario
            </label>
            <select
              value={filtroUsuario}
              onChange={(e) => setFiltroUsuario(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-linea-fuerte rounded-lg text-tinta"
            >
              <option value="">Todos los usuarios</option>
              {usuarios.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre} ({u.nombre_usuario})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-tenue block mb-1">
              Entidad
            </label>
            <select
              value={filtroModulo}
              onChange={(e) => setFiltroModulo(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-linea-fuerte rounded-lg text-tinta"
            >
              <option value="">Todas las entidades</option>
              <option value="usuario">Usuarios y sesión</option>
              <option value="propietario">Propietarios</option>
              <option value="apartaestudio">Apartaestudios</option>
              <option value="residente">Residentes</option>
              <option value="bloqueo">Bloqueos</option>
              <option value="contrato">Contratos</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-tenue block mb-1">
              Acción
            </label>
            <input
              type="text"
              placeholder="ej. contrato.crear"
              value={filtroAccion}
              onChange={(e) => setFiltroAccion(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-linea-fuerte rounded-lg text-tinta"
            />
          </div>

          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-tenue block mb-1">
              Desde
            </label>
            <input
              type="date"
              value={filtroFechaDesde}
              onChange={(e) => setFiltroFechaDesde(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-linea-fuerte rounded-lg text-tinta"
            />
          </div>

          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-tenue block mb-1">
              Hasta
            </label>
            <input
              type="date"
              value={filtroFechaHasta}
              onChange={(e) => setFiltroFechaHasta(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-linea-fuerte rounded-lg text-tinta"
            />
          </div>
        </div>
      </div>

      <p className="text-[11px] text-tenue">
        Mostrando {registros.length} de {total} eventos
      </p>

      {/* Tabla de Auditoría */}
      <Tabla
        columnas={columnas}
        datos={registros}
        cargando={cargando}
        error={error}
        alReintentar={cargarAuditoria}
        mensajeVacio="No se encontraron eventos de auditoría"
        subtituloVacio="Modifica los filtros de búsqueda o fecha para visualizar registros históricos."
      />

      {/* Modal Detalle de Evento */}
      <Modal
        abierto={Boolean(registroSeleccionado)}
        alCerrar={() => setRegistroSeleccionado(null)}
        titulo="Detalle del Evento de Auditoría"
        subtitulo={`Registro de trazabilidad #${registroSeleccionado?.id}`}
        tamano="md"
      >
        {registroSeleccionado && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 bg-fondo p-3 rounded text-xs border border-linea">
              <div>
                <span className="text-tenue block uppercase text-[10px]">Fecha y Hora</span>
                <span className="font-mono text-tinta">
                  {formatearFechaHoraCO(registroSeleccionado.momento)}
                </span>
              </div>
              <div>
                <span className="text-tenue block uppercase text-[10px]">Usuario Responsable</span>
                <span className="font-medium text-tinta">
                  {nombreUsuario(registroSeleccionado.usuario_id)}
                </span>
              </div>
              <div>
                <span className="text-tenue block uppercase text-[10px]">Entidad / Acción</span>
                <span className="font-medium text-tinta">
                  {registroSeleccionado.entidad} #{registroSeleccionado.entidad_id ?? '—'} → {registroSeleccionado.accion}
                </span>
              </div>
              <div>
                <span className="text-tenue block uppercase text-[10px]">IP Origen</span>
                <span className="font-mono text-tinta">
                  {registroSeleccionado.ip || '—'}
                </span>
              </div>
            </div>

            {(['valor_anterior', 'valor_nuevo'] as const).map((campo) =>
              registroSeleccionado[campo] ? (
                <div key={campo}>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-tenue block mb-1 flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5" />
                    {campo === 'valor_anterior' ? 'Valor anterior' : 'Valor nuevo'}
                  </span>
                  <pre className="text-[11px] font-mono bg-tinta text-sobre-tinta p-3 rounded overflow-x-auto max-h-48 border border-linea">
                    {JSON.stringify(registroSeleccionado[campo], null, 2)}
                  </pre>
                </div>
              ) : null
            )}

            <div className="flex justify-end pt-2">
              <Boton
                variante="secundario"
                tamano="sm"
                onClick={() => setRegistroSeleccionado(null)}
              >
                Cerrar
              </Boton>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
