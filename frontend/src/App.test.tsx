import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { App } from './App'

function renderizar(ruta = '/') {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter initialEntries={[ruta]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('App', () => {
  it('muestra que el servidor y la base de datos están disponibles', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ estado: 'ok', base_de_datos: 'ok' }), { status: 200 }),
    )
    renderizar()
    expect(await screen.findByText('Servidor y base de datos disponibles.')).toBeInTheDocument()
  })

  it('avisa cuando no hay conexión con el servidor', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'))
    renderizar()
    expect(await screen.findByText('No hay conexión con el servidor.')).toBeInTheDocument()
  })

  it('muestra la página no encontrada en rutas desconocidas', () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}'))
    renderizar('/no-existe')
    expect(screen.getByRole('heading', { name: 'Página no encontrada' })).toBeInTheDocument()
  })
})
