# Matriz de trazabilidad

Enlaza cada requisito con su regla, su módulo, sus criterios y sus pruebas. Un requisito solo
se marca **Probado** con pruebas ejecutadas y aprobadas.

Estados: Pendiente · Diseñado · Implementado · Probado (en el entorno de Claude) ·
Verificado (en el computador de Maryam) · Aprobado.

| Requisito | Reglas | Módulo | Criterios | Pruebas | Estado |
|---|---|---|---|---|---|
| RF-01 Autenticar y cerrar sesión | RU-01, RU-07, RU-08 | 1 Usuarios y sesión | U-01 a U-07, U-14, U-16 | `test_autenticacion.py` | Probado (backend) |
| RF-02 Gestión de usuarios | RU-02 a RU-06, RU-09 | 1 Usuarios y sesión | U-10, U-12, U-13, U-15 | `test_usuarios.py`, `test_comando_crear_admin.py` | Probado (backend) |
| RF-23 Auditoría inmodificable | — | 1 Usuarios y sesión (base) | U-17, U-18, P-12, R-12 | `test_auditoria.py`, `test_usuarios.py`, `test_propietarios.py`, `test_apartaestudios.py`, `test_residentes.py`, `test_bloqueos.py` | Probado para los módulos 1 a 3; se amplía en cada módulo |
| RNF-01 Hash seguro | RU-06 | 1 Usuarios y sesión | U-09 | `test_seguridad.py`, `test_autenticacion.py` | Probado |
| RNF-02 JWT en cookie y CSRF | RU-08 | 1 Usuarios y sesión | U-01, U-07, U-08 | `test_autenticacion.py`; U-08 en `frontend/src/api/cliente.test.ts` | Probado (backend); pantallas pendientes |
| RNF-03 Autorización en el servidor | — | 1 Usuarios y sesión | U-11, CA-16 | `test_permisos.py` | Probado; la tabla crece con cada módulo |
| RNF-04 Errores centralizados | — | Estructura base | — | `test_errores.py` | Probado |
| RNF-08 Dinero decimal exacto | — | Estructura base (tipo `Dinero`) | — | Se probará con cobros y pagos | Implementado |
| RNF-10 Fechas en hora de Bogotá | — | Estructura base | — | `test_tiempo.py`, `test_auditoria.py` | Probado |
| RNF-11 Separación y capas | — | Estructura base | — | Revisión de estructura | Implementado |
| RNF-12 OpenAPI | — | Estructura base | — | `test_errores.py` (documentación disponible) | Probado |
| RF-03 Propietarios y asociación de apartaestudios | RN-01, RP-01, RP-02, RP-06, RP-08 | 2 Propietarios y apartaestudios | P-01 a P-04, P-10, P-11 | `test_propietarios.py`, `test_apartaestudios.py`, `test_concurrencia_inmuebles.py` | Aprobado (backend) |
| RF-04 Registrar, editar y consultar apartaestudios | RP-03, RP-06, RP-07 | 2 Propietarios y apartaestudios | P-04, P-05, P-09 | `test_apartaestudios.py`, `test_normalizacion_inmuebles.py` | Aprobado (backend) |
| RF-05 Ocupación calculada y mantenimiento | RN-02, RN-03, RP-04, RP-05 | 2 Propietarios y apartaestudios | P-06 a P-08; CA-04 | `test_apartaestudios.py` | Aprobado sin contratos; CA-04 completo con el módulo 4 |
| RF-06 Directorio de residentes | RR-01, RR-02 | 3 Residentes y bloqueos | R-01 a R-04 | `test_residentes.py` | Aprobado (backend) |
| RF-07 Bloqueos con historial | RN-07, RR-03 a RR-06 | 3 Residentes y bloqueos | R-05 a R-11 | `test_bloqueos.py`, `test_concurrencia_bloqueos.py`, `test_permisos_bd.py` | Aprobado (backend); CA-03 con el módulo 4 |
| RNF-16 Datos personales | — | 3 Residentes y bloqueos (D-3) | R-11 | `test_bloqueos.py`, `test_residentes.py` | Motivos ocultos al empleado; política formal pendiente |
| RF-08 a RF-10 Contratos | RN-04 a RN-12 | 4 Contratos | C-01 a C-18; CA-01 a CA-04 | — | Diseñado |
| RF-11 a RF-18, RF-20 a RF-22 | RN-13 a RN-30 | Módulos 5 a 9 | CA-05 a CA-15, CA-17, CA-18 | — | Pendiente |
| ~~RF-19 Servicios públicos~~ | ~~RN-31~~ | — | — | — | Fuera del alcance |

## Cambios de alcance

| Fecha | Cambio | Decidido por |
|---|---|---|
| 2026-10-23 | Se retira el módulo de servicios públicos (RF-19, RN-31 y los 6 endpoints de medidores, lecturas y consumos): las lecturas de agua y energía se manejarán fuera del sistema. La API queda en 75 endpoints y la fase 8 en 9 módulos: usuarios, inmuebles, residentes, contratos, cobros, pagos, incrementos, mantenimiento y tablero | Maryam |
