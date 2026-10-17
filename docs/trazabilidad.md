# Matriz de trazabilidad

Enlaza cada requisito con su regla, su módulo, sus criterios y sus pruebas. Un requisito solo
se marca **Probado** con pruebas ejecutadas y aprobadas.

Estados: Pendiente · Diseñado · Implementado · Probado (en el entorno de Claude) ·
Verificado (en el computador de Maryam) · Aprobado.

| Requisito | Reglas | Módulo | Criterios | Pruebas | Estado |
|---|---|---|---|---|---|
| RF-01 Autenticar y cerrar sesión | RU-01, RU-07, RU-08 | 1 Usuarios y sesión | U-01 a U-07, U-14, U-16 | `test_autenticacion.py` | Probado (backend) |
| RF-02 Gestión de usuarios | RU-02 a RU-06, RU-09 | 1 Usuarios y sesión | U-10, U-12, U-13, U-15 | `test_usuarios.py`, `test_comando_crear_admin.py` | Probado (backend) |
| RF-23 Auditoría inmodificable | — | 1 Usuarios y sesión (base) | U-17, U-18 | `test_auditoria.py`, `test_usuarios.py` | Probado para el módulo 1; se amplía en cada módulo |
| RNF-01 Hash seguro | RU-06 | 1 Usuarios y sesión | U-09 | `test_seguridad.py`, `test_autenticacion.py` | Probado |
| RNF-02 JWT en cookie y CSRF | RU-08 | 1 Usuarios y sesión | U-01, U-07, U-08 | `test_autenticacion.py`; U-08 en `frontend/src/api/cliente.test.ts` | Probado (backend); pantallas pendientes |
| RNF-03 Autorización en el servidor | — | 1 Usuarios y sesión | U-11, CA-16 | `test_permisos.py` | Probado; la tabla crece con cada módulo |
| RNF-04 Errores centralizados | — | Fase 7 | — | `test_errores.py` | Probado |
| RNF-08 Dinero decimal exacto | — | Fase 7 (tipo `Dinero`) | — | Se probará con cobros y pagos | Implementado |
| RNF-10 Fechas en hora de Bogotá | — | Fase 7 | — | `test_tiempo.py`, `test_auditoria.py` | Probado |
| RNF-11 Separación y capas | — | Fase 7 | — | Revisión de estructura | Implementado |
| RNF-12 OpenAPI | — | Fase 7 | — | `test_errores.py` (documentación disponible) | Probado |
| RF-03 a RF-22 | RN-01 a RN-31 | Módulos 2 en adelante | CA-01 a CA-15, CA-17, CA-18 | — | Pendiente |
