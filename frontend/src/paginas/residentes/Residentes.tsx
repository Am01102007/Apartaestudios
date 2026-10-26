import React, { useEffect, useState, useCallback } from 'react';
import {
  listarResidentes,
  obtenerResidente,
  crearResidente,
  actualizarResidente,
  obtenerContratosResidente,
} from '../../api/residentes';
import {
  Contrato,
  Residente,
  ResidenteCrear,
  ResidenteDetalle,
  TipoDocumento,
} from '../../api/tipos';
import { Tabla, Columna } from '../../componentes/Tabla';
import { Boton } from '../../componentes/Boton';
import { Modal } from '../../componentes/Modal';
import { Campo, EntradaTexto, EntradaSeleccion } from '../../componentes/Campo';
import { InsigniaEstado } from '../../componentes/InsigniaEstado';
import { useAuth } from '../../contexto/AuthContext';
import { ErrorApi } from '../../api/cliente';
import { formatearFechaCO, formatearMonedaCOP, vaciosANulo } from '../../utilidades/formato';
import { OpcionesDocumento } from '../../componentes/OpcionesDocumento';
import {
  Plus,
  Search,
  Eye,
  Edit2,
  ShieldAlert,
  Phone,
  Mail,
  User,
  HeartHandshake,
} from 'lucide-react';

interface FormularioResidente {
  tipo_documento: TipoDocumento;
  numero_documento: string;
  nombre: string;
  telefono: string;
  correo: string;
  contacto_emergencia_nombre: string;
  contacto_emergencia_telefono: string;
  notas: string;
}

const FORMULARIO_VACIO: FormularioResidente = {
  tipo_documento: 'CC',
  numero_documento: '',
  nombre: '',
  telefono: '',
  correo: '',
  contacto_emergencia_nombre: '',
  contacto_emergencia_telefono: '',
  notas: '',
};

export const PaginaResidentes: React.FC = () => {
  const [residentes, setResidentes] = useState<Residente[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState('');

  // Modales
  const [modalFormularioAbierto, setModalFormularioAbierto] = useState(false);
  const [modalDetalleAbierto, setModalDetalleAbierto] = useState(false);

  // Seleccionado
  const [residenteSeleccionado, setResidenteSeleccionado] = useState<Residente | null>(null);
  const [detalleResidente, setDetalleResidente] = useState<ResidenteDetalle | null>(null);
  const [contratosResidente, setContratosResidente] = useState<Contrato[]>([]);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);

  // Formulario
  const [guardando, setGuardando] = useState(false);
  const [formulario, setFormulario] = useState<FormularioResidente>(FORMULARIO_VACIO);
  const [erroresCampos, setErroresCampos] = useState<Record<string, string>>({});

  const { agregarNotificacion } = useAuth();

  const cargarResidentes = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await listarResidentes({ texto: busqueda.trim() || undefined });
      setResidentes(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar residentes';
      setError(msg);
    } finally {
      setCargando(false);
    }
  }, [busqueda]);

  useEffect(() => {
    cargarResidentes();
  }, [cargarResidentes]);

  const abrirCrear = () => {
    setResidenteSeleccionado(null);
    setFormulario(FORMULARIO_VACIO);
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirEditar = (r: Residente) => {
    setResidenteSeleccionado(r);
    setFormulario({
      tipo_documento: r.tipo_documento,
      numero_documento: r.numero_documento,
      nombre: r.nombre,
      telefono: r.telefono,
      correo: r.correo || '',
      contacto_emergencia_nombre: r.contacto_emergencia_nombre || '',
      contacto_emergencia_telefono: r.contacto_emergencia_telefono || '',
      notas: r.notas || '',
    });
    setErroresCampos({});
    setModalFormularioAbierto(true);
  };

  const abrirDetalle = async (r: Residente) => {
    setResidenteSeleccionado(r);
    setModalDetalleAbierto(true);
    setCargandoDetalle(true);
    try {
      const [detalle, contratos] = await Promise.all([
        obtenerResidente(r.id),
        obtenerContratosResidente(r.id),
      ]);
      setDetalleResidente(detalle);
      setContratosResidente(contratos);
    } catch {
      agregarNotificacion('error', 'Error al cargar detalle del residente');
    } finally {
      setCargandoDetalle(false);
    }
  };

  const guardarResidente = async (e: React.FormEvent) => {
    e.preventDefault();
    setErroresCampos({});

    const errs: Record<string, string> = {};
    if (!formulario.numero_documento.trim()) errs.numero_documento = 'El número de documento es obligatorio';
    if (!formulario.nombre.trim()) errs.nombre = 'El nombre completo es obligatorio';
    if (!formulario.telefono.trim()) errs.telefono = 'El teléfono de contacto es obligatorio';
    if (formulario.correo.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formulario.correo)) {
      errs.correo = 'Formato de correo inválido';
    }

    if (Object.keys(errs).length > 0) {
      setErroresCampos(errs);
      return;
    }

    setGuardando(true);
    try {
      if (residenteSeleccionado) {
        await actualizarResidente(residenteSeleccionado.id, vaciosANulo(formulario));
        agregarNotificacion('exito', 'Residente actualizado exitosamente');
      } else {
        await crearResidente(vaciosANulo<ResidenteCrear>(formulario));
        agregarNotificacion('exito', 'Residente registrado exitosamente');
      }
      setModalFormularioAbierto(false);
      cargarResidentes();
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

  const columnas: Columna<Residente>[] = [
    {
      clave: 'documento',
      encabezado: 'Identificación',
      render: (r) => (
        <span className="font-semibold text-xs text-[#0B0B0C] dark:text-[#FAFAF9]">
          {r.tipo_documento} {r.numero_documento}
        </span>
      ),
    },
    {
      clave: 'nombre',
      encabezado: 'Nombre Completo',
      render: (r) => (
        <div>
          <span className="font-medium text-sm text-[#0B0B0C] dark:text-[#FAFAF9]">
            {r.nombre}
          </span>
          <p className="text-xs text-[#8A8D91] flex items-center gap-1">
            <Mail className="w-3 h-3" /> {r.correo || '—'}
          </p>
        </div>
      ),
    },
    {
      clave: 'telefono',
      encabezado: 'Teléfono',
      render: (r) => (
        <span className="text-xs text-[#5A5D62] dark:text-[#A0A3A8] flex items-center gap-1">
          <Phone className="w-3 h-3 text-[#8A8D91]" /> {r.telefono}
        </span>
      ),
    },
    {
      clave: 'acciones',
      encabezado: 'Acciones',
      alineacion: 'derecha',
      render: (r) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => abrirDetalle(r)}
            title="Ver detalle, bloqueo y contratos"
            className="p-1.5 text-[#5A5D62] hover:text-[#0B0B0C] dark:text-[#A0A3A8] dark:hover:text-white rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => abrirEditar(r)}
            title="Editar residente"
            className="p-1.5 text-[#5A5D62] hover:text-[#0B0B0C] dark:text-[#A0A3A8] dark:hover:text-white rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Edit2 className="w-4 h-4" />
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
            Directorio de Arrendatarios
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
            Residentes
          </h1>
        </div>
        <Boton variante="plata" onClick={abrirCrear} icono={<Plus className="w-4 h-4" />}>
          Registrar Residente
        </Boton>
      </div>

      {/* Filtros */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white dark:bg-[#141416] p-3 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-[#8A8D91] absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por cédula, nombre o correo..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-transparent border-0 outline-none text-[#0B0B0C] dark:text-[#FAFAF9] placeholder-[#8A8D91]"
          />
        </div>

      </div>

      {/* Tabla */}
      <Tabla
        columnas={columnas}
        datos={residentes}
        cargando={cargando}
        error={error}
        alReintentar={cargarResidentes}
        mensajeVacio="No hay residentes registrados"
        subtituloVacio="Registra residentes para generar contratos de arrendamiento."
      />

      {/* Modal Crear / Editar */}
      <Modal
        abierto={modalFormularioAbierto}
        alCerrar={() => setModalFormularioAbierto(false)}
        titulo={residenteSeleccionado ? 'Editar Residente' : 'Registrar Nuevo Residente'}
        subtitulo="Datos de identificación ciudadana, teléfono y contacto de emergencia."
        tamano="lg"
      >
        <form onSubmit={guardarResidente} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Campo label="Tipo Documento" obligatorio error={erroresCampos.tipo_documento} id="tipo_doc">
              <EntradaSeleccion
                id="tipo_doc"
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
                id="num_doc"
              >
                <EntradaTexto
                  id="num_doc"
                  placeholder="ej. 1017234567"
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
            label="Nombre Completo"
            obligatorio
            error={erroresCampos.nombre}
            id="nom_comp"
          >
            <EntradaTexto
              id="nom_comp"
              placeholder="ej. Juliana Gómez Montoya"
              value={formulario.nombre}
              onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })}
              tieneError={Boolean(erroresCampos.nombre)}
            />
          </Campo>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Campo label="Teléfono / Celular" obligatorio error={erroresCampos.telefono} id="tel_res">
              <EntradaTexto
                id="tel_res"
                placeholder="ej. 3009876543"
                value={formulario.telefono}
                onChange={(e) => setFormulario({ ...formulario, telefono: e.target.value })}
                tieneError={Boolean(erroresCampos.telefono)}
              />
            </Campo>

            <Campo label="Correo Electrónico" error={erroresCampos.correo} id="mail_res">
              <EntradaTexto
                id="mail_res"
                type="email"
                placeholder="ej. juliana@correo.com"
                value={formulario.correo}
                onChange={(e) => setFormulario({ ...formulario, correo: e.target.value })}
                tieneError={Boolean(erroresCampos.correo)}
              />
            </Campo>
          </div>

          {/* Contacto de emergencia */}
          <div className="pt-2">
            <p className="text-[11px] font-semibold tracking-widest uppercase text-[#8A8D91] mb-2 flex items-center gap-1.5">
              <HeartHandshake className="w-3.5 h-3.5" /> Contacto de Emergencia
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-[#FAFAF9] dark:bg-[#1A1A1D] p-3 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
              <Campo label="Nombre del Contacto" id="contacto_emergencia_nombre" error={erroresCampos.contacto_emergencia_nombre}>
                <EntradaTexto
                  id="contacto_emergencia_nombre"
                  placeholder="ej. Juan Gómez (Padre)"
                  value={formulario.contacto_emergencia_nombre}
                  onChange={(e) =>
                    setFormulario({ ...formulario, contacto_emergencia_nombre: e.target.value })
                  }
                />
              </Campo>

              <Campo label="Teléfono del Contacto" id="contacto_emergencia_telefono" error={erroresCampos.contacto_emergencia_telefono}>
                <EntradaTexto
                  id="contacto_emergencia_telefono"
                  placeholder="ej. 3154567890"
                  value={formulario.contacto_emergencia_telefono}
                  onChange={(e) =>
                    setFormulario({ ...formulario, contacto_emergencia_telefono: e.target.value })
                  }
                />
              </Campo>
            </div>
          </div>

          <Campo label="Notas" id="notas_res" error={erroresCampos.notas}>
            <EntradaTexto
              id="notas_res"
              placeholder="Observaciones internas (opcional)"
              value={formulario.notas}
              onChange={(e) => setFormulario({ ...formulario, notas: e.target.value })}
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
              {residenteSeleccionado ? 'Guardar Cambios' : 'Registrar Residente'}
            </Boton>
          </div>
        </form>
      </Modal>

      {/* Modal Detalle con Bloqueo y Contratos */}
      <Modal
        abierto={modalDetalleAbierto}
        alCerrar={() => setModalDetalleAbierto(false)}
        titulo="Expediente del Residente"
        subtitulo="Verificación de antecedentes de bloqueo y contratos históricos."
        tamano="lg"
      >
        {cargandoDetalle ? (
          <div className="py-12 text-center text-xs text-[#8A8D91] uppercase tracking-wider">
            Cargando historial del residente...
          </div>
        ) : detalleResidente ? (
          <div className="space-y-6">
            {/* Alerta si está bloqueado */}
            {detalleResidente.bloqueo_activo && (
              <div className="p-4 bg-[#FCF4F5] dark:bg-[#251013] border border-[#7A1F2B]/40 rounded-[4px] flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-[#7A1F2B] dark:text-[#EFA3AC] shrink-0 mt-0.5" />
                <div className="text-xs text-[#7A1F2B] dark:text-[#EFA3AC] leading-relaxed">
                  <span className="font-semibold block uppercase tracking-wider">
                    Persona con Bloqueo Activo en el Sistema
                  </span>
                  <p className="mt-1 font-medium">
                    Motivo:{' '}
                    {detalleResidente.bloqueo_activo.motivo || 'Motivo reservado'}
                  </p>
                  <p className="mt-0.5 text-[11px] opacity-80">
                    Bloqueado el: {formatearFechaCO(detalleResidente.bloqueo_activo.bloqueado_en)}
                  </p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-[#FAFAF9] dark:bg-[#1A1A1D] p-4 rounded-[4px] border border-[#E3E4E6] dark:border-[#2A2A2E]">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">Identificación</p>
                <p className="text-sm font-semibold text-[#0B0B0C] dark:text-[#FAFAF9] mt-0.5">
                  {detalleResidente.nombre}
                </p>
                <p className="text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
                  {detalleResidente.tipo_documento} {detalleResidente.numero_documento}
                </p>
              </div>

              <div>
                <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">Contacto</p>
                <p className="text-xs text-[#0B0B0C] dark:text-[#FAFAF9] mt-0.5">
                  Tel: {detalleResidente.telefono}
                </p>
                <p className="text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
                  Correo: {detalleResidente.correo || '—'}
                </p>
              </div>

              {detalleResidente.contacto_emergencia_nombre && (
                <div className="sm:col-span-2 pt-2 border-t border-[#E3E4E6] dark:border-[#2A2A2E]">
                  <p className="text-[10px] uppercase tracking-widest text-[#8A8D91]">
                    Contacto de Emergencia
                  </p>
                  <p className="text-xs text-[#0B0B0C] dark:text-[#FAFAF9] mt-0.5">
                    {detalleResidente.contacto_emergencia_nombre} (Tel: {detalleResidente.contacto_emergencia_telefono || 'No registrado'})
                  </p>
                </div>
              )}
            </div>

            {/* Contratos asociados */}
            <div>
              <h4 className="font-serif-luxury text-base font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mb-3">
                Contratos de Arrendamiento ({contratosResidente.length})
              </h4>

              {contratosResidente.length > 0 ? (
                <div className="divide-y divide-[#E3E4E6] dark:divide-[#2A2A2E] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] overflow-hidden bg-white dark:bg-[#141416]">
                  {contratosResidente.map((c) => (
                    <div key={c.id} className="p-3.5 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-[#0B0B0C] dark:text-[#FAFAF9]">
                            Contrato #{c.id}
                          </span>
                          <span className="text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
                            · Apto {c.apartaestudio.codigo}
                          </span>
                        </div>
                        <div className="text-[11px] text-[#8A8D91] mt-0.5">
                          Periodo: {formatearFechaCO(c.fecha_inicio)} al {formatearFechaCO(c.fecha_terminacion)} · Canon: {formatearMonedaCOP(c.canon_vigente)}
                        </div>
                      </div>
                      <InsigniaEstado tipo="contrato" valor={c.estado} tamano="sm" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-[#8A8D91] bg-[#FAFAF9] dark:bg-[#1A1A1D] rounded-[4px] border border-dashed border-[#C0C0C0] dark:border-[#3A3A3E]">
                  No existen contratos asociados a este residente.
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
