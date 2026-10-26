/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexto/AuthContext';
import { RutaProtegida } from './componentes/RutaProtegida';
import { DisenoPrincipal } from './componentes/DisenoPrincipal';

// Páginas de Autenticación
import { PaginaIngresar } from './paginas/auth/Ingresar';
import { PaginaCambiarContrasena } from './paginas/auth/CambiarContrasena';

// Módulos
import { PaginaInicio } from './paginas/inicio/Inicio';
import { PaginaPropietarios } from './paginas/propietarios/Propietarios';
import { PaginaApartaestudios } from './paginas/apartaestudios/Apartaestudios';
import { PaginaResidentes } from './paginas/residentes/Residentes';
import { PaginaBloqueos } from './paginas/bloqueos/Bloqueos';
import { PaginaContratos } from './paginas/contratos/Contratos';
import { PaginaUsuarios } from './paginas/usuarios/Usuarios';
import { PaginaAuditoria } from './paginas/auditoria/Auditoria';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Ruta pública de acceso */}
          <Route path="/ingresar" element={<PaginaIngresar />} />

          {/* Cambio de contraseña (protegida, sin menú lateral si es obligatoria) */}
          <Route
            path="/cambiar-contrasena"
            element={
              <RutaProtegida>
                <div className="min-h-screen bg-[#FAFAF9] dark:bg-[#0B0B0C] p-4 flex items-center justify-center">
                  <PaginaCambiarContrasena />
                </div>
              </RutaProtegida>
            }
          />

          {/* Rutas protegidas dentro del diseño principal con barra lateral */}
          <Route
            path="/"
            element={
              <RutaProtegida>
                <DisenoPrincipal />
              </RutaProtegida>
            }
          >
            <Route index element={<PaginaInicio />} />
            <Route path="propietarios" element={<PaginaPropietarios />} />
            <Route path="apartaestudios" element={<PaginaApartaestudios />} />
            <Route path="residentes" element={<PaginaResidentes />} />
            <Route path="bloqueos" element={<PaginaBloqueos />} />
            <Route path="contratos" element={<PaginaContratos />} />

            {/* Módulos solo para rol administrador */}
            <Route
              path="usuarios"
              element={
                <RutaProtegida requiereAdmin>
                  <PaginaUsuarios />
                </RutaProtegida>
              }
            />
            <Route
              path="auditoria"
              element={
                <RutaProtegida requiereAdmin>
                  <PaginaAuditoria />
                </RutaProtegida>
              }
            />
          </Route>

          {/* Redirección por defecto */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
