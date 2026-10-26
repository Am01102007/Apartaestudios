/**
 * Utilidades de formato para Colombia
 */

const formateadorMoneda = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
});

// La API envía los montos como texto decimal ("1200000.00") para no perder precisión.
export function formatearMonedaCOP(monto: number | string | null | undefined): string {
  if (monto === null || monto === undefined || monto === '') return '—';
  const valor = typeof monto === 'string' ? Number(monto) : monto;
  if (isNaN(valor)) return '—';
  return formateadorMoneda.format(valor);
}

export function formatearFechaCO(fechaStr: string | null | undefined): string {
  if (!fechaStr) return '—';
  try {
    // Si viene en formato YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(fechaStr)) {
      const [anio, mes, dia] = fechaStr.split('-');
      return `${dia}/${mes}/${anio}`;
    }

    const fecha = new Date(fechaStr);
    if (isNaN(fecha.getTime())) return fechaStr;

    return new Intl.DateTimeFormat('es-CO', {
      timeZone: 'America/Bogota',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(fecha);
  } catch {
    return fechaStr;
  }
}

export function formatearFechaHoraCO(fechaStr: string | null | undefined): string {
  if (!fechaStr) return '—';
  try {
    const fecha = new Date(fechaStr);
    if (isNaN(fecha.getTime())) return fechaStr;

    return new Intl.DateTimeFormat('es-CO', {
      timeZone: 'America/Bogota',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    }).format(fecha);
  } catch {
    return fechaStr;
  }
}

export function obtenerFechaHoyCO(): string {
  // Retorna YYYY-MM-DD en America/Bogota
  const ahora = new Date();
  const opciones: Intl.DateTimeFormatOptions = {
    timeZone: 'America/Bogota',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  };
  const partes = new Intl.DateTimeFormat('en-CA', opciones).formatToParts(ahora);
  const anio = partes.find((p) => p.type === 'year')?.value || '2026';
  const mes = partes.find((p) => p.type === 'month')?.value || '01';
  const dia = partes.find((p) => p.type === 'day')?.value || '01';
  return `${anio}-${mes}-${dia}`;
}

/** Convierte los textos vacíos de un formulario en null, como espera la API en campos opcionales. */
export function vaciosANulo<R>(datos: object): R {
  const resultado: Record<string, unknown> = {};
  for (const [clave, valor] of Object.entries(datos)) {
    resultado[clave] = typeof valor === 'string' && valor.trim() === '' ? null : valor;
  }
  return resultado as R;
}
