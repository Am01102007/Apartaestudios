import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { UsuarioActual } from '../api/tipos';
import { obtenerYo, login as apiLogin, logout as apiLogout } from '../api/auth';
import { configurarListenersCliente } from '../api/cliente';

interface NotificacionItem {
  id: string;
  tipo: 'error' | 'advertencia' | 'info' | 'exito';
  mensaje: string;
}

interface ContextoAuthTipo {
  usuario: UsuarioActual | null;
  cargando: boolean;
  esAdmin: boolean;
  debeCambiarContrasena: boolean;
  iniciarSesion: (nombre_usuario: string, contrasena: string) => Promise<UsuarioActual>;
  cerrarSesion: () => Promise<void>;
  refrescarSesion: () => Promise<void>;
  notificaciones: NotificacionItem[];
  agregarNotificacion: (tipo: 'error' | 'advertencia' | 'info' | 'exito', mensaje: string) => void;
  eliminarNotificacion: (id: string) => void;
  temaOscuro: boolean;
  alternarTema: () => void;
}

const AuthContext = createContext<ContextoAuthTipo | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [usuario, setUsuario] = useState<UsuarioActual | null>(null);
  const [cargando, setCargando] = useState<boolean>(true);
  const [notificaciones, setNotificaciones] = useState<NotificacionItem[]>([]);
  const [temaOscuro, setTemaOscuro] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('tema_aura') === 'dark';
    }
    return false;
  });

  const alternarTema = () => {
    setTemaOscuro((prev) => {
      const nuevo = !prev;
      if (typeof window !== 'undefined') {
        localStorage.setItem('tema_aura', nuevo ? 'dark' : 'light');
        if (nuevo) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
      return nuevo;
    });
  };

  useEffect(() => {
    if (temaOscuro) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [temaOscuro]);

  const agregarNotificacion = useCallback(
    (tipo: 'error' | 'advertencia' | 'info' | 'exito', mensaje: string) => {
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      setNotificaciones((prev) => [...prev, { id, tipo, mensaje }]);
      setTimeout(() => {
        setNotificaciones((prev) => prev.filter((n) => n.id !== id));
      }, 5000);
    },
    []
  );

  const eliminarNotificacion = useCallback((id: string) => {
    setNotificaciones((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const refrescarSesion = useCallback(async () => {
    try {
      const datosYo = await obtenerYo();
      setUsuario(datosYo);
    } catch {
      setUsuario(null);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    // Configurar listeners globales del cliente HTTP
    configurarListenersCliente(
      (tipo, mensaje) => {
        agregarNotificacion(tipo, mensaje);
      },
      () => {
        // En 401: no guardamos tokens, simplemente limpiamos el usuario en React
        setUsuario(null);
      }
    );

    // Cargar sesión inicial llamando a GET /api/v1/auth/yo
    refrescarSesion();
  }, [agregarNotificacion, refrescarSesion]);

  const iniciarSesion = async (nombre_usuario: string, contrasena: string): Promise<UsuarioActual> => {
    const usuarioAutenticado = await apiLogin(nombre_usuario, contrasena);
    setUsuario(usuarioAutenticado);
    return usuarioAutenticado;
  };

  const cerrarSesion = async () => {
    try {
      await apiLogout();
    } catch {
      // Ignorar error al cerrar sesión
    } finally {
      setUsuario(null);
    }
  };

  const esAdmin = usuario?.rol === 'administrador';
  const debeCambiarContrasena = Boolean(usuario?.debe_cambiar_contrasena);

  return (
    <AuthContext.Provider
      value={{
        usuario,
        cargando,
        esAdmin,
        debeCambiarContrasena,
        iniciarSesion,
        cerrarSesion,
        refrescarSesion,
        notificaciones,
        agregarNotificacion,
        eliminarNotificacion,
        temaOscuro,
        alternarTema,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser utilizado dentro de un AuthProvider');
  }
  return context;
}
