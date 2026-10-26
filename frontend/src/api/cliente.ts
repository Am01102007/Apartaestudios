import { ErrorDetalle, ErrorItem } from './tipos';

export class ErrorApi extends Error {
  public codigo: string;
  public detalles: ErrorItem[];
  public status: number;

  constructor(status: number, error: ErrorDetalle) {
    super(error.mensaje || 'Ha ocurrido un error en el servidor');
    this.name = 'ErrorApi';
    this.codigo = error.codigo || 'ERROR_DESCONOCIDO';
    this.detalles = error.detalles || [];
    this.status = status;
  }

  public obtenerErrorCampo(nombreCampo: string): string | undefined {
    return this.detalles.find((d) => d.campo === nombreCampo)?.mensaje;
  }
}

type ListenerNotificacion = (tipo: 'error' | 'advertencia' | 'info', mensaje: string) => void;
type ListenerNoAutorizado = () => void;

let listenerNotificacion: ListenerNotificacion | null = null;
let listenerNoAutorizado: ListenerNoAutorizado | null = null;

export function configurarListenersCliente(
  onNotificar?: ListenerNotificacion,
  onNoAutorizado?: ListenerNoAutorizado
) {
  if (onNotificar) listenerNotificacion = onNotificar;
  if (onNoAutorizado) listenerNoAutorizado = onNoAutorizado;
}

function obtenerCookie(nombre: string): string | null {
  if (typeof document === 'undefined') return null;
  const coincidencia = document.cookie.match(new RegExp('(^|;\\s*)(' + nombre + ')=([^;]*)'));
  return coincidencia ? decodeURIComponent(coincidencia[3]) : null;
}

export async function clienteHttp<T>(
  endpoint: string,
  opciones: RequestInit = {}
): Promise<T> {
  const ruta = endpoint.startsWith('/') ? `/api/v1${endpoint}` : `/api/v1/${endpoint}`;
  const metodo = (opciones.method || 'GET').toUpperCase();
  const headers = new Headers(opciones.headers || {});

  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // En POST, PATCH, PUT y DELETE, leer la cookie csrf_token y mandarla en X-CSRF-Token
  if (['POST', 'PATCH', 'PUT', 'DELETE'].includes(metodo)) {
    const csrfToken = obtenerCookie('csrf_token');
    if (csrfToken) {
      headers.set('X-CSRF-Token', csrfToken);
    }
    if (!headers.has('Content-Type') && opciones.body) {
      headers.set('Content-Type', 'application/json');
    }
  }

  let respuesta: Response;
  try {
    respuesta = await fetch(ruta, {
      ...opciones,
      method: metodo,
      headers,
      credentials: 'same-origin', // Cookie HttpOnly
    });
  } catch (err) {
    const mensajeRed = 'Error de conexión con el servidor. Verifica que el servicio esté activo.';
    if (listenerNotificacion) {
      listenerNotificacion('error', mensajeRed);
    }
    throw new ErrorApi(0, {
      codigo: 'ERROR_CONEXION',
      mensaje: mensajeRed,
      detalles: [],
    });
  }

  // Manejo de códigos especiales
  if (respuesta.status === 401) {
    if (listenerNoAutorizado) {
      listenerNoAutorizado();
    }
  }

  if (respuesta.status === 403) {
    const mensaje403 = 'No tienes permiso para esta acción';
    if (listenerNotificacion) {
      listenerNotificacion('error', mensaje403);
    }
  }

  if (respuesta.status === 429) {
    const mensaje429 = 'Demasiadas solicitudes. Por favor espera un momento e intenta de nuevo.';
    if (listenerNotificacion) {
      listenerNotificacion('advertencia', mensaje429);
    }
  }

  if (!respuesta.ok) {
    let errorJson: { error?: ErrorDetalle } | null = null;
    try {
      errorJson = await respuesta.json();
    } catch {
      // No era JSON
    }

    const detalle: ErrorDetalle = errorJson?.error || {
      codigo: `HTTP_${respuesta.status}`,
      mensaje: respuesta.status === 403 
        ? 'No tienes permiso para esta acción'
        : respuesta.status === 429
        ? 'Demasiadas solicitudes. Por favor espera un momento e intenta de nuevo.'
        : `Error en la solicitud (${respuesta.status})`,
      detalles: [],
    };

    const errorApi = new ErrorApi(respuesta.status, detalle);
    // Mostrar mensaje en aviso global a menos que sea 401
    if (respuesta.status !== 401 && listenerNotificacion && detalle.mensaje) {
      listenerNotificacion('error', detalle.mensaje);
    }
    throw errorApi;
  }

  if (respuesta.status === 204) {
    return {} as T;
  }

  return (await respuesta.json()) as T;
}
