import { describe, expect, it, vi } from 'vitest'
import { ErrorApi, solicitar } from './cliente'

function respuestaJson(estado: number, cuerpo: unknown) {
  return new Response(JSON.stringify(cuerpo), {
    status: estado,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('cliente de la API', () => {
  it('envía el token CSRF de la cookie en las operaciones que modifican datos', async () => {
    document.cookie = 'csrf_token=abc123; path=/'
    const fetchSimulado = vi.spyOn(globalThis, 'fetch').mockResolvedValue(respuestaJson(200, {}))

    await solicitar('/pagos', { method: 'POST', body: JSON.stringify({ valor: 1 }) })

    const [ruta, opciones] = fetchSimulado.mock.calls[0]
    expect(ruta).toBe('/api/v1/pagos')
    expect(new Headers(opciones?.headers).get('X-CSRF-Token')).toBe('abc123')
    expect(opciones?.credentials).toBe('same-origin')
  })

  it('no envía el token CSRF en las consultas', async () => {
    document.cookie = 'csrf_token=abc123; path=/'
    const fetchSimulado = vi.spyOn(globalThis, 'fetch').mockResolvedValue(respuestaJson(200, {}))

    await solicitar('/salud')

    expect(new Headers(fetchSimulado.mock.calls[0][1]?.headers).has('X-CSRF-Token')).toBe(false)
  })

  it('convierte el formato único de error en ErrorApi', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      respuestaJson(409, {
        error: { codigo: 'ocupado', mensaje: 'El apartaestudio está ocupado.', detalles: [] },
      }),
    )

    const error = await solicitar('/contratos', { method: 'POST', body: '{}' }).catch((e) => e)

    expect(error).toBeInstanceOf(ErrorApi)
    expect(error).toMatchObject({ estado: 409, codigo: 'ocupado', message: 'El apartaestudio está ocupado.' })
  })

  it('informa la falta de conexión', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(solicitar('/salud')).rejects.toMatchObject({ estado: 0, codigo: 'sin_conexion' })
  })

  it('no guarda nada en el almacenamiento del navegador', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(respuestaJson(200, { estado: 'ok' }))

    await solicitar('/salud')

    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })
})
