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
        <span className="text-xs font-mono text-[#0B0B0C] dark:text-[#FAFAF9]">
          {formatearFechaHoraCO(r.momento)}
        </span>
      ),
    },
    {
      clave: 'usuario',
      encabezado: 'Usuario',
      render: (r) => (
        <div>
          <span className="font-semibold text-xs text-[#0B0B0C] dark:text-[#FAFAF9]">
            {nombreUsuario(r.usuario_id)}
          </span>
        </div>
      ),
    },
    {
      clave: 'modulo',
      encabezado: 'Entidad',
      render: (r) => (
        <span className="text-xs font-medium px-2 py-0.5 rounded bg-[#F4F5F6] dark:bg-[#1E1E22] text-[#1A1A1D] dark:text-[#FAFAF9] border border-[#E3E4E6] dark:border-[#2A2A2E] uppercase">
          {r.entidad}
        </span>
      ),
    },
    {
      clave: 'accion',
      encabezado: 'Acción Ejecutada',
      render: (r) => (
        <span className="text-xs font-semibold uppercase tracking-wider text-[#0B0B0C] dark:text-[#FAFAF9]">
          {r.accion}
        </span>
      ),
    },
    {
      clave: 'entidad_id',
      encabezado: 'Registro',
      render: (r) => (
        <span className="text-xs font-mono text-[#5A5D62] dark:text-[#A0A3A8]">
          {r.entidad_id ? `#${r.entidad_id}` : '—'}
        </span>
      ),
    },
    {
      clave: 'ip',
      encabezado: 'IP Origen',
      render: (r) => (
        <span className="text-[11px] font-mono text-[#8A8D91]">
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
          className="p-1.5 text-[#5A5D62] hover:text-[#0B0B0C] dark:text-[#A0A3A8] dark:hover:text-white rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
        >
          <Eye className="w-4 h-4" />
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-[#E3E4E6] dark:border-[#2A2A2E]">
        <div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-[#8A8D91]">
            Trazabilidad & Cumplimiento (Solo Administrador)
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
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
      <div className="bg-white dark:bg-[#141416] p-4 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E] space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#E3E4E6] dark:border-[#2A2A2E]">
          <span className="text-[10px] font-semibold tracking-widest uppercase text-[#8A8D91] flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5" /> Filtros de Auditoría
          </span>
          <button
            onClick={limpiarFiltros}
            className="text-xs text-[#8A8D91] hover:text-[#0B0B0C] dark:hover:text-white"
          >
            Limpiar filtros
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-[#8A8D91] block mb-1">
              Usuario
            </label>
            <select
              value={filtroUsuario}
              onChange={(e) => setFiltroUsuario(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
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
            <label className="text-[10px] font-medium uppercase tracking-wider text-[#8A8D91] block mb-1">
              Entidad
            </label>
            <select
              value={filtroModulo}
              onChange={(e) => setFiltroModulo(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
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
            <label className="text-[10px] font-medium uppercase tracking-wider text-[#8A8D91] block mb-1">
              Acción
            </label>
            <input
              type="text"
              placeholder="ej. contrato.crear"
              value={filtroAccion}
              onChange={(e) => setFiltroAccion(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
            />
          </div>

          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-[#8A8D91] block mb-1">
              Desde
            </label>
            <input
              type="date"
              value={filtroFechaDesde}
              onChange={(e) => setFiltroFechaDesde(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
            />
          </div>

          <div>
            <label className="text-[10px] font-medium uppercase tracking-wider text-[#8A8D91] block mb-1">
              Hasta
            </label>
            <input
              type="date"
              value={filtroFechaHasta}
              onChange={(e) => setFiltroFechaHasta(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-transparent border border-[#C0C0C0] dark:border-[#3A3A3E] rounded-[4px] text-[#0B0B0C] dark:text-[#FAFAF9]"
            />
          </div>
        </div>
      </div>

      <p className="text-[11px] text-[#8A8D91]">
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
            <div className="grid grid-cols-2 gap-3 bg-[#FAFAF9] dark:bg-[#1A1A1D] p-3 rounded text-xs border border-[#E3E4E6] dark:border-[#2A2A2E]">
              <div>
                <span className="text-[#8A8D91] block uppercase text-[10px]">Fecha y Hora</span>
                <span className="font-mono text-[#0B0B0C] dark:text-[#FAFAF9]">
                  {formatearFechaHoraCO(registroSeleccionado.momento)}
                </span>
              </div>
              <div>
                <span className="text-[#8A8D91] block uppercase text-[10px]">Usuario Responsable</span>
                <span className="font-medium text-[#0B0B0C] dark:text-[#FAFAF9]">
                  {nombreUsuario(registroSeleccionado.usuario_id)}
                </span>
              </div>
              <div>
                <span className="text-[#8A8D91] block uppercase text-[10px]">Entidad / Acción</span>
                <span className="font-medium text-[#0B0B0C] dark:text-[#FAFAF9]">
                  {registroSeleccionado.entidad} #{registroSeleccionado.entidad_id ?? '—'} → {registroSeleccionado.accion}
                </span>
              </div>
              <div>
                <span className="text-[#8A8D91] block uppercase text-[10px]">IP Origen</span>
                <span className="font-mono text-[#0B0B0C] dark:text-[#FAFAF9]">
                  {registroSeleccionado.ip || '—'}
                </span>
              </div>
            </div>

            {(['valor_anterior', 'valor_nuevo'] as const).map((campo) =>
              registroSeleccionado[campo] ? (
                <div key={campo}>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#8A8D91] block mb-1 flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5" />
                    {campo === 'valor_anterior' ? 'Valor anterior' : 'Valor nuevo'}
                  </span>
                  <pre className="text-[11px] font-mono bg-[#0B0B0C] text-[#FAFAF9] p-3 rounded overflow-x-auto max-h-48 border border-[#2A2A2E]">
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
