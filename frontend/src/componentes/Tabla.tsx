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
    <div className="w-full bg-panel border border-linea rounded-lg shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-linea bg-fondo">
              {columnas.map((col) => (
                <th
                  key={col.clave}
                  style={col.ancho ? { width: col.ancho } : undefined}
                  className={`px-4 py-3.5 text-[11px] font-semibold uppercase tracking-widest text-tinta-2 ${
                    alinearClases[col.alineacion || 'izquierda']
                  }`}
                >
                  {col.encabezado}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-linea text-sm ">
            {cargando ? (
              <tr>
                <td colSpan={columnas.length} className="px-6 py-16 text-center">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <Loader2 className="w-6 h-6 animate-spin text-tenue" />
                    <span className="text-xs uppercase tracking-wider text-tinta-2">
                      Cargando información...
                    </span>
                  </div>
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={columnas.length} className="px-6 py-14 text-center">
                  <div className="flex flex-col items-center justify-center gap-3 max-w-md mx-auto">
                    <div className="w-10 h-10 rounded-full bg-peligro-bg flex items-center justify-center text-peligro">
                      <AlertCircle className="w-5 h-5" />
                    </div>
                    <h4 className="text-sm font-medium text-peligro">
                      Error al cargar los datos
                    </h4>
                    <p className="text-xs text-tinta-2">{error}</p>
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
                    <div className="w-10 h-10 rounded-full bg-sutil flex items-center justify-center text-tenue mb-1">
                      <Inbox className="w-5 h-5" />
                    </div>
                    <h4 className="text-sm font-medium text-tinta">
                      {mensajeVacio}
                    </h4>
                    <p className="text-xs text-tenue">{subtituloVacio}</p>
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
                    className="hover:bg-fondo transition-colors"
                  >
                    {columnas.map((col) => (
                      <td
                        key={col.clave}
                        className={`px-4 py-3.5 text-tinta ${
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
