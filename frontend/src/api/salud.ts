import { solicitar } from './cliente'

export interface EstadoSalud {
  estado: 'ok' | 'degradado'
  base_de_datos: 'ok' | 'sin_conexion'
}

export const consultarSalud = () => solicitar<EstadoSalud>('/salud')
