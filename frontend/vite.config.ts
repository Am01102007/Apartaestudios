import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// En desarrollo, Vite reenvía /api al backend. Así el navegador ve un solo origen, igual
// que en producción, y las cookies SameSite=Strict funcionan sin abrir CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: false },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/pruebas/configuracion.ts'],
  },
})
