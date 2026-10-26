import { afterEach, describe, expect, it, vi } from 'vitest';
import { clienteHttp, ErrorApi } from './cliente';

function respuestaJson(estado: number, cuerpo: unknown) {
  return new Response(JSON.stringify(cuerpo), {
    status: estado,
    headers: { 'Content-Type': 'application/json' },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
});

describe('cliente de la API', () => {
  it('envía el token CSRF de la cookie en las operaciones que modifican datos', async () => {
    document.cookie = 'csrf_token=abc123; path=/';
    const fetchSimulado = vi.spyOn(globalThis, 'fetch').mockResolvedValue(respuestaJson(200, {}));

    await clienteHttp('/contratos', { method: 'PATCH', body: JSON.stringify({ notas: 'x' }) });

    const [ruta, opciones] = fetchSimulado.mock.calls[0];
    expect(ruta).toBe('/api/v1/contratos');
    expect(new Headers(opciones?.headers).get('X-CSRF-Token')).toBe('abc123');
    expect(opciones?.credentials).toBe('same-origin');
  });

  it('no envía el token CSRF en las consultas', async () => {
    document.cookie = 'csrf_token=abc123; path=/';
    const fetchSimulado = vi.spyOn(globalThis, 'fetch').mockResolvedValue(respuestaJson(200, {}));

    await clienteHttp('/salud');

    expect(new Headers(fetchSimulado.mock.calls[0][1]?.headers).has('X-CSRF-Token')).toBe(false);
  });

  it('convierte el formato único de error en ErrorApi', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      respuestaJson(409, {
        error: { codigo: 'ocupado', mensaje: 'El apartaestudio está ocupado.', detalles: [] },
      })
    );

    const error = await clienteHttp('/contratos', { method: 'POST', body: '{}' }).catch((e) => e);

    expect(error).toBeInstanceOf(ErrorApi);
    expect(error).toMatchObject({ status: 409, codigo: 'ocupado', message: 'El apartaestudio está ocupado.' });
  });

  it('no guarda nada en el almacenamiento del navegador', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(respuestaJson(200, { estado: 'ok' }));

    await clienteHttp('/salud');

    expect(sessionStorage.length).toBe(0);
    expect(Object.keys(localStorage).filter((k) => k !== 'tema_aura')).toHaveLength(0);
  });
});
