/** Arma "?a=1&b=2" omitiendo valores vacíos. */
export function consulta(parametros: Record<string, string | number | boolean | undefined | null>) {
  const params = new URLSearchParams();
  for (const [clave, valor] of Object.entries(parametros)) {
    if (valor !== undefined && valor !== null && valor !== '') params.append(clave, String(valor));
  }
  const texto = params.toString();
  return texto ? `?${texto}` : '';
}

export const enviar = (method: 'POST' | 'PATCH', datos?: unknown): RequestInit => ({
  method,
  body: datos === undefined ? undefined : JSON.stringify(datos),
});
