/**
 * Cliente HTTP de la API.
 *
 * - La sesión viaja en una cookie HttpOnly que el navegador envía solo; este código nunca
 *   ve ni guarda el token (nada de localStorage ni sessionStorage).
 * - En las operaciones que modifican datos se envía el token CSRF, leído de la cookie
 *   legible `csrf_token`, en la cabecera X-CSRF-Token.
 * - Los errores del servidor llegan con el formato único {"error": {...}} y se convierten
 *   en ErrorApi.
 */

export const BASE_API = '/api/v1'
const COOKIE_CSRF = 'csrf_token'
const METODOS_QUE_MODIFICAN = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

export interface DetalleError {
  campo?: string
  mensaje?: string
  tipo?: string
}

export class ErrorApi extends Error {
  readonly estado: number
  readonly codigo: string
  readonly detalles: DetalleError[]

  constructor(estado: number, codigo: string, mensaje: string, detalles: DetalleError[] = []) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
    this.codigo = codigo
    this.detalles = detalles
  }
}

export function leerCookie(nombre: string): string | null {
  for (const parte of document.cookie.split(';')) {
    const [clave, ...valor] = parte.trim().split('=')
    if (clave === nombre) return decodeURIComponent(valor.join('='))
  }
  return null
}

export async function solicitar<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const metodo = (opciones.method ?? 'GET').toUpperCase()
  const cabeceras = new Headers(opciones.headers)
  cabeceras.set('Accept', 'application/json')
  if (opciones.body !== undefined && !(opciones.body instanceof FormData)) {
    cabeceras.set('Content-Type', 'application/json')
  }
  if (METODOS_QUE_MODIFICAN.has(metodo)) {
    const csrf = leerCookie(COOKIE_CSRF)
    if (csrf) cabeceras.set('X-CSRF-Token', csrf)
  }

  let respuesta: Response
  try {
    respuesta = await fetch(`${BASE_API}${ruta}`, {
      ...opciones,
      method: metodo,
      headers: cabeceras,
      credentials: 'same-origin',
    })
  } catch {
    throw new ErrorApi(0, 'sin_conexion', 'No fue posible conectar con el servidor.')
  }

  const cuerpo: unknown = respuesta.status === 204 ? null : await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    const error = (cuerpo as { error?: { codigo?: string; mensaje?: string; detalles?: DetalleError[] } } | null)?.error
    throw new ErrorApi(
      respuesta.status,
      error?.codigo ?? 'error_http',
      error?.mensaje ?? 'Ocurrió un error inesperado.',
      error?.detalles ?? [],
    )
  }
  return cuerpo as T
}
