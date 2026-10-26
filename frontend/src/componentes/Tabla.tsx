import React from 'react';
import { Loader2, AlertCircle, Inbox, RefreshCw } from 'lucide-react';
import { Boton } from './Boton';

export interface Columna<T> {
  clave: string;
  encabezado: string;
  render?: (fila: T) => React.ReactNode;
  ancho?: string;
  alineacion?: 'izquierda' | 'centro' | 'derecha';
}

interface TablaProps<T> {
  columnas: Columna<T>[];
  datos: T[];
  cargando?: boolean;
  error?: string | null;
  alReintentar?: () => void;
  mensajeVacio?: string;
  subtituloVacio?: string;
  accionVacio?: React.ReactNode;
  identificadorFila?: (fila: T, index: number) => string;
}

export function Tabla<T>({
  columnas,
  datos,
  cargando = false,
  error = null,
  alReintentar,
  mensajeVacio = 'No se encontraron registros',
  subtituloVacio = 'Actualmente no hay elementos disponibles con los criterios seleccionados.',
  accionVacio,
  identificadorFila,
}: TablaProps<T>) {
  const alinearClases = {
    izquierda: 'text-left',
    centro: 'text-center',
    derecha: 'text-right',
  };

  return (
    <div className="w-full bg-white dark:bg-[#141416] border border-[#E3E4E6] dark:border-[#2A2A2E] rounded-[4px] shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[#E3E4E6] dark:border-[#2A2A2E] bg-[#FAFAF9] dark:bg-[#18181B]">
              {columnas.map((col) => (
                <th
                  key={col.clave}
                  style={col.ancho ? { width: col.ancho } : undefined}
                  className={`px-4 py-3.5 text-[11px] font-semibold uppercase tracking-widest text-[#5A5D62] dark:text-[#A0A3A8] ${
                    alinearClases[col.alineacion || 'izquierda']
                  }`}
                >
                  {col.encabezado}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E3E4E6] dark:divide-[#242428] text-sm font-sans-clean">
            {cargando ? (
              <tr>
                <td colSpan={columnas.length} className="px-6 py-16 text-center">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <Loader2 className="w-6 h-6 animate-spin text-[#8A8D91]" />
                    <span className="text-xs uppercase tracking-wider text-[#5A5D62] dark:text-[#A0A3A8]">
                      Cargando información...
                    </span>
                  </div>
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={columnas.length} className="px-6 py-14 text-center">
                  <div className="flex flex-col items-center justify-center gap-3 max-w-md mx-auto">
                    <div className="w-10 h-10 rounded-full bg-[#FCF4F5] dark:bg-[#2E1015] flex items-center justify-center text-[#7A1F2B] dark:text-[#E89AA3]">
                      <AlertCircle className="w-5 h-5" />
                    </div>
                    <h4 className="text-sm font-medium text-[#7A1F2B] dark:text-[#E89AA3]">
                      Error al cargar los datos
                    </h4>
                    <p className="text-xs text-[#5A5D62] dark:text-[#A0A3A8]">{error}</p>
                    {alReintentar && (
                      <Boton
                        tamano="sm"
                        variante="secundario"
                        onClick={alReintentar}
                        icono={<RefreshCw className="w-3.5 h-3.5" />}
                        className="mt-2"
                      >
                        Reintentar
                      </Boton>
                    )}
                  </div>
                </td>
              </tr>
            ) : datos.length === 0 ? (
              <tr>
                <td colSpan={columnas.length} className="px-6 py-16 text-center">
                  <div className="flex flex-col items-center justify-center gap-2 max-w-sm mx-auto">
                    <div className="w-10 h-10 rounded-full bg-[#F4F5F6] dark:bg-[#1E1E22] flex items-center justify-center text-[#8A8D91] mb-1">
                      <Inbox className="w-5 h-5" />
                    </div>
                    <h4 className="text-sm font-medium text-[#1A1A1D] dark:text-[#FAFAF9]">
                      {mensajeVacio}
                    </h4>
                    <p className="text-xs text-[#8A8D91]">{subtituloVacio}</p>
                    {accionVacio && <div className="mt-3">{accionVacio}</div>}
                  </div>
                </td>
              </tr>
            ) : (
              datos.map((fila, index) => {
                const id = identificadorFila
                  ? identificadorFila(fila, index)
                  : ((fila as { id?: string }).id ?? String(index));
                return (
                  <tr
                    key={id}
                    className="hover:bg-[#FAFAF9] dark:hover:bg-[#1A1A1D] transition-colors"
                  >
                    {columnas.map((col) => (
                      <td
                        key={col.clave}
                        className={`px-4 py-3.5 text-[#0B0B0C] dark:text-[#FAFAF9] ${
                          alinearClases[col.alineacion || 'izquierda']
                        }`}
                      >
                        {col.render
                          ? col.render(fila)
                          : String((fila as Record<string, unknown>)[col.clave] ?? '—')}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
