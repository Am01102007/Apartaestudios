import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarApartaestudios } from '../../api/apartaestudios';
import { listarContratos } from '../../api/contratos';
import { listarBloqueos } from '../../api/bloqueos';
import { Apartaestudio, Contrato, Bloqueo, estadoApartaestudio } from '../../api/tipos';
import {
  Building2,
  Lock,
  Wrench,
  FileCheck2,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { Boton } from '../../componentes/Boton';
import { InsigniaEstado } from '../../componentes/InsigniaEstado';
import { formatearMonedaCOP, formatearFechaCO } from '../../utilidades/formato';

export const PaginaInicio: React.FC = () => {
  const [apartaestudios, setApartaestudios] = useState<Apartaestudio[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [bloqueos, setBloqueos] = useState<Bloqueo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargarDatos = async () => {
    setCargando(true);
    setError(null);
    try {
      const [respAparta, respContratos, respBloqueos] = await Promise.all([
        listarApartaestudios(),
        listarContratos(),
        listarBloqueos({ estado: 'activos' }),
      ]);
      setApartaestudios(respAparta);
      setContratos(respContratos);
      setBloqueos(respBloqueos);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar métricas del sistema';
      setError(msg);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  // Cálculos solicitados en el requerimiento:
  // "tarjetas con totales calculados a partir de los listados: apartaestudios libres, ocupados y en mantenimiento; contratos vigentes; personas bloqueadas."
  const apartaestudiosLibres = apartaestudios.filter((a) => a.activo && estadoApartaestudio(a) === 'libre').length;
  const apartaestudiosOcupados = apartaestudios.filter((a) => a.activo && estadoApartaestudio(a) === 'ocupado').length;
  const apartaestudiosMantenimiento = apartaestudios.filter((a) => a.activo && estadoApartaestudio(a) === 'mantenimiento').length;
  const contratosVigentes = contratos.filter((c) => c.estado === 'vigente');
  const personasBloqueadas = bloqueos.filter((b) => b.activo).length;

  const totalCanonEstimado = contratosVigentes.reduce((acc, curr) => acc + Number(curr.canon_vigente), 0);

  return (
    <div className="space-y-8">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-[#E3E4E6] dark:border-[#2A2A2E]">
        <div>
          <span className="text-[11px] font-semibold tracking-widest uppercase text-[#8A8D91]">
            Panel de Control General
          </span>
          <h1 className="text-2xl sm:text-3xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9] mt-1">
            Resumen Operativo
          </h1>
        </div>
        <Boton
          variante="secundario"
          tamano="sm"
          onClick={cargarDatos}
          cargando={cargando}
          icono={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Actualizar Indicadores
        </Boton>
      </div>

      {error && (
        <div className="p-4 bg-[#FCF4F5] dark:bg-[#251013] border border-[#7A1F2B]/40 rounded-[4px] text-xs text-[#7A1F2B] dark:text-[#EFA3AC]">
          {error}
        </div>
      )}

      {/* Tarjetas de Totales */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Libres */}
        <div className="bg-white dark:bg-[#141416] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between text-[#8A8D91] mb-2">
            <span className="text-[10px] tracking-widest uppercase font-semibold">Libres</span>
            <Building2 className="w-4 h-4 text-[#8A8D91]" />
          </div>
          <div className="text-3xl font-serif-luxury font-medium text-[#1A1A1D] dark:text-[#FAFAF9]">
            {cargando ? '—' : apartaestudiosLibres}
          </div>
          <div className="mt-2 text-xs text-[#5A5D62] dark:text-[#A0A3A8]">
            Apartaestudios disponibles
          </div>
        </div>

        {/* Ocupados */}
        <div className="bg-[#0B0B0C] text-[#FAFAF9] border border-[#2A2A2E] rounded-[4px] p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between text-[#C0C0C0] mb-2">
            <span className="text-[10px] tracking-widest uppercase font-semibold">Ocupados</span>
            <Lock className="w-4 h-4 text-[#C0C0C0]" />
          </div>
          <div className="text-3xl font-serif-luxury font-medium text-white">
            {cargando ? '—' : apartaestudiosOcupados}
          </div>
          <div className="mt-2 text-xs text-[#8A8D91]">Con residente activo</div>
        </div>

        {/* Mantenimiento */}
        <div className="bg-white dark:bg-[#141416] border border-[#8A8D91] dark:border-[#3A3A3E] rounded-[4px] p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between text-[#8A8D91] mb-2">
            <span className="text-[10px] tracking-widest uppercase font-semibold">Mantenimiento</span>
            <Wrench className="w-4 h-4 text-[#8A8D91]" />
          </div>
          <div className="text-3xl font-serif-luxury font-medium text-[#1A1A1D] dark:text-[#FAFAF9]">
            {cargando ? '—' : apartaestudiosMantenimiento}
          </div>
          <div className="mt-2 text-xs text-[#5A5D62] dark:text-[#A0A3A8]">En revisión o daño</div>
        </div>

        {/* Contratos Vigentes */}
        <div className="bg-white dark:bg-[#141416] border border-[#2F4F4A]/30 dark:border-[#2F4F4A]/40 rounded-[4px] p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between text-[#2F4F4A] dark:text-[#84C9BE] mb-2">
            <span className="text-[10px] tracking-widest uppercase font-semibold">Vigentes</span>
            <FileCheck2 className="w-4 h-4" />
          </div>
          <div className="text-3xl font-serif-luxury font-medium text-[#2F4F4A] dark:text-[#84C9BE]">
            {cargando ? '—' : contratosVigentes.length}
          </div>
          <div className="mt-2 text-xs text-[#5A5D62] dark:text-[#A0A3A8]">Contratos activos</div>
        </div>

        {/* Personas Bloqueadas */}
        <div className="bg-white dark:bg-[#141416] border border-[#7A1F2B]/30 dark:border-[#7A1F2B]/40 rounded-[4px] p-5 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between text-[#7A1F2B] dark:text-[#E89AA3] mb-2">
            <span className="text-[10px] tracking-widest uppercase font-semibold">Bloqueadas</span>
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="text-3xl font-serif-luxury font-medium text-[#7A1F2B] dark:text-[#E89AA3]">
            {cargando ? '—' : personasBloqueadas}
          </div>
          <div className="mt-2 text-xs text-[#5A5D62] dark:text-[#A0A3A8]">Con restricción activa</div>
        </div>
      </div>

      {/* Indicador de Cartera / Renta Mensual */}
      <div className="bg-white dark:bg-[#141416] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-[4px] bg-[#111113] text-[#FAFAF9] border border-[#3A3A3E] flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-[#C0C0C0]" />
          </div>
          <div>
            <span className="text-[10px] tracking-widest uppercase text-[#8A8D91] font-semibold">
              Canon Mensual Comprometido (COP)
            </span>
            <h3 className="text-2xl font-serif-luxury font-medium text-[#0B0B0C] dark:text-[#FAFAF9]">
              {formatearMonedaCOP(totalCanonEstimado)}
            </h3>
          </div>
        </div>
        <div className="text-xs text-[#5A5D62] dark:text-[#A0A3A8] max-w-sm">
          Calculado sobre los {contratosVigentes.length} contratos actualmente vigentes en la
          plataforma.
        </div>
      </div>

      {/* Listados de Resumen */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Últimos Contratos Vigentes */}
        <div className="bg-white dark:bg-[#141416] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] p-6 shadow-xs">
          <div className="flex items-center justify-between pb-4 border-b border-[#E3E4E6] dark:border-[#2A2A2E] mb-4">
            <h3 className="font-serif-luxury text-lg font-medium text-[#0B0B0C] dark:text-[#FAFAF9]">
              Contratos Recientes
            </h3>
            <Link
              to="/contratos"
              className="text-xs uppercase tracking-wider text-[#5A5D62] dark:text-[#C0C0C0] hover:text-[#0B0B0C] dark:hover:text-white inline-flex items-center gap-1 font-semibold"
            >
              Ver todos <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {contratos.slice(0, 4).map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between p-3 rounded-[4px] bg-[#FAFAF9] dark:bg-[#1A1A1D] border border-[#E3E4E6] dark:border-[#2A2A2E]"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-[#0B0B0C] dark:text-[#FAFAF9]">
                      Apto {c.apartaestudio.codigo}
                    </span>
                    <span className="text-[11px] text-[#8A8D91]">• {c.residente.nombre}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-[#5A5D62] dark:text-[#A0A3A8] mt-1">
                    <span>Canon: {formatearMonedaCOP(c.canon_vigente)}</span>
                    <span className="inline-flex items-center gap-1">
                      <Clock className="w-3 h-3 text-[#8A8D91]" />
                      Fin: {formatearFechaCO(c.fecha_terminacion)}
                    </span>
                  </div>
                </div>
                <InsigniaEstado tipo="contrato" valor={c.estado} tamano="sm" />
              </div>
            ))}
            {contratos.length === 0 && (
              <p className="text-xs text-[#8A8D91] py-4 text-center">No hay contratos registrados</p>
            )}
          </div>
        </div>

        {/* Apartaestudios destacados */}
        <div className="bg-white dark:bg-[#141416] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] p-6 shadow-xs">
          <div className="flex items-center justify-between pb-4 border-b border-[#E3E4E6] dark:border-[#2A2A2E] mb-4">
            <h3 className="font-serif-luxury text-lg font-medium text-[#0B0B0C] dark:text-[#FAFAF9]">
              Estado de Inmuebles
            </h3>
            <Link
              to="/apartaestudios"
              className="text-xs uppercase tracking-wider text-[#5A5D62] dark:text-[#C0C0C0] hover:text-[#0B0B0C] dark:hover:text-white inline-flex items-center gap-1 font-semibold"
            >
              Gestionar <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {apartaestudios.slice(0, 4).map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between p-3 rounded-[4px] bg-[#FAFAF9] dark:bg-[#1A1A1D] border border-[#E3E4E6] dark:border-[#2A2A2E]"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-[#0B0B0C] dark:text-[#FAFAF9]">
                      Unidad {a.codigo}
                    </span>
                    <span className="text-[11px] text-[#8A8D91]">
                      {a.propietario.nombre}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#5A5D62] dark:text-[#A0A3A8] mt-1">
                    {a.direccion}{a.area_m2 ? ` · ${Number(a.area_m2)} m²` : ''}
                  </div>
                </div>
                <InsigniaEstado tipo="apartaestudio" valor={estadoApartaestudio(a)} tamano="sm" />
              </div>
            ))}
            {apartaestudios.length === 0 && (
              <p className="text-xs text-[#8A8D91] py-4 text-center">No hay apartaestudios creados</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
