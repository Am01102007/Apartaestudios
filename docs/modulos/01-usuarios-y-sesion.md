# Módulo 1. Usuarios y sesión

Estado: **backend implementado y probado; pendiente de tu verificación y aprobación.** Las pantallas se harán en la etapa de frontend, por decisión de Maryam (backend primero, por módulos).
Fecha: 2026-10-17.

Cubre: RF-01, RF-02, RF-23 (solo la base de la auditoría), RNF-01, RNF-02, RNF-03, CA-16 y CA-17.
Se apoya en las decisiones aprobadas en [decisiones-fases-3-a-6.md](../decisiones-fases-3-a-6.md).

---

## 1. Objetivo y alcance

Que solo las personas autorizadas entren al sistema y que cada una pueda hacer únicamente lo
que su rol permite. Es el primer módulo porque todos los demás dependen de saber quién hace
cada operación.

**Incluye**
- Inicio y cierre de sesión con JWT en cookie segura y protección CSRF.
- Consulta del usuario actual y cambio de la propia contraseña.
- Gestión de usuarios por el administrador: crear, consultar, editar, desactivar y reactivar.
- Restablecimiento de contraseña por el administrador (ver decisión D-2).
- Bloqueo temporal tras intentos fallidos.
- Control de permisos por rol en el servidor, reutilizable por todos los módulos.
- Tabla de auditoría inmodificable y su registro para las operaciones de este módulo.
- Consulta del registro de auditoría por el administrador (`GET /auditoria`).
- Comando de consola para crear el primer administrador.

**No incluye**
- Recuperación de contraseña por correo (el MVP no envía correos).
- Autenticación de dos factores.
- Parámetros del sistema e IPC (`/configuracion`, `/ipc`): van con el módulo de incrementos.
- Pantallas (inicio de sesión, cambio de contraseña, gestión de usuarios): etapa de frontend.

---

## 2. Requisitos y criterios de aceptación

| ID | Criterio | Cubre |
|---|---|---|
| U-01 | Con nombre de usuario y contraseña correctos, `POST /auth/login` responde 200, crea la cookie de sesión `HttpOnly` y la cookie CSRF, y no devuelve el token en el cuerpo | RF-01, RNF-02 |
| U-02 | Con contraseña incorrecta, o con un usuario que no existe, la respuesta es la misma: 401 con el mensaje "Usuario o contraseña incorrectos" | RF-01 |
| U-03 | Tras 5 intentos fallidos seguidos, la cuenta no puede entrar durante 15 minutos aunque la contraseña sea correcta; pasado ese tiempo sí puede | RF-01 |
| U-04 | Un usuario desactivado no puede iniciar sesión, y sus sesiones abiertas dejan de funcionar de inmediato | RF-02 |
| U-05 | Después de cerrar sesión, la cookie anterior no sirve aunque alguien la haya copiado | RF-01 |
| U-06 | Una sesión sin uso durante 30 minutos expira; ninguna sesión dura más de 12 horas | RNF-02 |
| U-07 | Una petición `POST`, `PATCH` o `DELETE` sin cabecera `X-CSRF-Token` válida se rechaza con 403 | RNF-02, CA-17 |
| U-08 | El frontend no guarda el token ni datos de sesión en `localStorage` ni `sessionStorage` | RNF-02, CA-17 |
| U-09 | La base de datos guarda solo el hash Argon2id de la contraseña; ningún endpoint ni registro devuelve el hash | RNF-01 |
| U-10 | Una contraseña de menos de 10 caracteres o igual al nombre de usuario se rechaza con 422 | RNF-01 |
| U-11 | Un empleado que llama cualquier endpoint de administrador recibe 403 (prueba automática que recorre todos los endpoints con cada rol) | RNF-03, CA-16 |
| U-12 | No se puede crear un usuario con un nombre de usuario ya registrado, aunque cambien mayúsculas | RF-02 |
| U-13 | No se puede desactivar ni pasar a empleado al último administrador activo | RF-02 |
| U-14 | Cambiar la propia contraseña exige la contraseña actual y cierra las demás sesiones del usuario | RF-01 |
| U-15 | Cambiar el rol, desactivar o restablecer la contraseña de un usuario cierra todas sus sesiones | RF-02 |
| U-16 | Un usuario con contraseña restablecida solo puede usar el cambio de contraseña hasta que la cambie | RF-02 |
| U-17 | Cada operación de la sección 5 marcada con "Audita" deja un registro con autor, momento, acción, entidad, valores anterior y nuevo (sin contraseñas) e IP | RF-23 |
| U-18 | Un `UPDATE` o `DELETE` directo sobre la tabla de auditoría falla en la base de datos | RF-23 |

---

## 3. Reglas de negocio

| ID | Regla |
|---|---|
| RU-01 | Se inicia sesión con el nombre de usuario: de 3 a 30 caracteres entre letras sin tilde, números, punto, guion y guion bajo; único sin distinguir mayúsculas y guardado en minúsculas. El correo es un dato de contacto opcional |
| RU-02 | Roles: `administrador` y `empleado`. Cada usuario tiene exactamente uno |
| RU-03 | Los usuarios no se eliminan; se desactivan y se reactivan (propuesta aprobada, sección 4) |
| RU-04 | Debe existir siempre al menos un administrador activo |
| RU-05 | Un administrador no puede desactivarse ni cambiarse el rol a sí mismo |
| RU-06 | Contraseña: entre 10 y 128 caracteres, distinta del nombre de usuario. No se exigen mezclas de símbolos (la longitud protege más y es más fácil de recordar) |
| RU-07 | 5 intentos fallidos seguidos bloquean el ingreso de la cuenta 15 minutos. Un ingreso exitoso reinicia el contador |
| RU-08 | La sesión expira tras 30 minutos sin uso o 12 horas desde el ingreso, lo que ocurra primero |
| RU-09 | El restablecimiento lo hace un administrador, que asigna una contraseña temporal; el usuario debe cambiarla al entrar |

---

## 4. Cambios en el modelo de datos

Migración `0002_usuarios_sesiones_auditoria`.

**`usuarios`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| nombre | VARCHAR(120) | obligatorio |
| nombre_usuario | VARCHAR(30) | único; se guarda en minúsculas |
| correo | VARCHAR(254) | opcional, solo de contacto |
| hash_contrasena | VARCHAR(255) | Argon2id |
| rol | VARCHAR(20) | `CHECK (rol IN ('administrador','empleado'))` |
| activo | BOOLEAN | por defecto verdadero |
| debe_cambiar_contrasena | BOOLEAN | verdadero tras un restablecimiento |
| intentos_fallidos | SMALLINT | por defecto 0 |
| bloqueado_hasta | TIMESTAMPTZ | nulo si no está bloqueado |
| ultimo_ingreso | TIMESTAMPTZ | |
| creado_en, actualizado_en | TIMESTAMPTZ | |

**`sesiones`**

| Columna | Tipo | Notas |
|---|---|---|
| id | VARCHAR(64) | identificador aleatorio de 256 bits; va dentro del JWT |
| usuario_id | BIGINT | FK a `usuarios` |
| hash_csrf | VARCHAR(64) | SHA-256 del token CSRF; el token en claro solo lo tiene el navegador |
| creada_en | TIMESTAMPTZ | |
| ultimo_uso | TIMESTAMPTZ | se actualiza como mucho una vez por minuto para no escribir en cada petición |
| expira_en | TIMESTAMPTZ | creada_en + 12 h |
| cerrada_en | TIMESTAMPTZ | nulo mientras está abierta |
| motivo_cierre | VARCHAR(30) | `logout`, `desactivado`, `cambio_contrasena`, `cambio_rol`, `restablecimiento` |
| ip, agente_usuario | VARCHAR | para auditoría |

**`auditoria`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| momento | TIMESTAMPTZ | por defecto `now()` |
| usuario_id | BIGINT | FK, nulo en intentos de ingreso con un usuario inexistente |
| accion | VARCHAR(60) | por ejemplo `usuario.crear`, `sesion.ingreso_fallido` |
| entidad, entidad_id | VARCHAR(60), VARCHAR(60) | |
| valor_anterior, valor_nuevo | JSONB | nunca incluye contraseñas ni hashes |
| ip | VARCHAR(45) | |

Disparador `auditoria_inmodificable`: rechaza `UPDATE` y `DELETE` sobre `auditoria`.

**Por qué una tabla de sesiones si se usa JWT.** Un JWT por sí solo no se puede invalidar antes
de que expire. Guardar la sesión en el servidor permite que cerrar sesión, desactivar un usuario
o cambiar su contraseña tenga efecto inmediato (U-04, U-05, U-15), a cambio de una consulta por
petición.

---

## 5. Endpoints y permisos

Todos bajo `/api/v1`. "CSRF" indica que exige la cabecera `X-CSRF-Token`.

| Método | Ruta | Rol | CSRF | Audita | Descripción |
|---|---|---|---|---|---|
| POST | /auth/login | Público | No | Sí | Valida credenciales y crea la sesión |
| POST | /auth/logout | Ambos | Sí | Sí | Cierra la sesión actual |
| GET | /auth/yo | Ambos | No | No | Usuario actual, rol y si debe cambiar la contraseña |
| POST | /auth/cambiar-contrasena | Ambos | Sí | Sí | Cambia la propia contraseña |
| GET | /usuarios | Admin | No | No | Lista con filtros por rol y estado |
| POST | /usuarios | Admin | Sí | Sí | Crea un usuario con contraseña temporal |
| GET | /usuarios/{id} | Admin | No | No | Detalle |
| PATCH | /usuarios/{id} | Admin | Sí | Sí | Edita nombre, nombre de usuario, correo o rol |
| POST | /usuarios/{id}/desactivar | Admin | Sí | Sí | Desactiva y cierra sus sesiones |
| POST | /usuarios/{id}/activar | Admin | Sí | Sí | Reactiva |
| POST | /usuarios/{id}/restablecer-contrasena | Admin | Sí | Sí | **Nuevo** (D-2): asigna contraseña temporal |
| GET | /auditoria | Admin | No | No | Registro con filtros por usuario, acción, entidad y fechas |

`POST /auth/login` también tiene límite por dirección IP (20 intentos por minuto) para frenar
ataques contra muchas cuentas a la vez.

---

## 6. Archivos creados o modificados

Durante la implementación, usuarios y sesiones quedaron en un solo dominio (`usuarios`): el
inicio de sesión necesita el estado del usuario (intentos, bloqueo) y la gestión de usuarios
necesita cerrar sesiones. Separarlos creaba una dependencia circular entre dos dominios.

**Nuevos (backend)**

| Archivo | Propósito |
|---|---|
| `app/core/seguridad.py` | Hash Argon2id, tokens aleatorios, firma y lectura de JWT |
| `app/core/limite.py` | Límite de intentos de ingreso por IP (en memoria) |
| `app/api/dependencias.py` | Dependencias comunes: base de datos, configuración, reloj, IP |
| `app/modulos/usuarios/modelos.py` | Tablas `usuarios` y `sesiones` |
| `app/modulos/usuarios/esquemas.py` | Entradas y salidas; rechaza campos desconocidos |
| `app/modulos/usuarios/repositorio.py` | Consultas y cierre masivo de sesiones |
| `app/modulos/usuarios/servicio.py` | Gestión de usuarios (RU-03 a RU-06, RU-09) |
| `app/modulos/usuarios/autenticacion.py` | Ingreso, validación de sesión, cierre y cambio de contraseña (RU-07, RU-08) |
| `app/modulos/usuarios/dependencias.py` | `SesionActual`, `SesionAdministrador`, `requiere_rol(...)` y CSRF, para todos los módulos |
| `app/modulos/usuarios/router_auth.py` | `/auth/*` |
| `app/modulos/usuarios/router.py` | `/usuarios/*` |
| `app/modulos/auditoria/{modelos,esquemas,repositorio,servicio,router}.py` | Tabla `auditoria`, registro y `GET /auditoria` |
| `app/comandos/crear_admin.py` | `python -m app.comandos.crear_admin` |
| `alembic/versions/0002_usuarios_sesiones_auditoria.py` | Tablas, índices y disparador de la auditoría |
| `tests/unit/test_seguridad.py` | Pruebas unitarias de seguridad y configuración |
| `tests/integration/test_{autenticacion,usuarios,auditoria,permisos,comando_crear_admin}.py`, `ayudas.py` | Pruebas de integración |

**Modificados**: `app/main.py`, `app/api/router.py`, `app/core/config.py`, `app/core/errores.py`
(errores 422 y 429 de servicio), `app/db/modelos.py`, `pyproject.toml`, `.env.example`,
`tests/conftest.py` (reloj de prueba y clientes independientes), README.

---

## 7. Implementación por etapas

| Etapa | Estado |
|---|---|
| 1. Migración 0002 y modelos | Hecha |
| 2. Núcleo de seguridad | Hecha |
| 3. Sesión, bloqueo, CSRF y dependencias de permisos | Hecha |
| 4. Gestión de usuarios y restablecimiento | Hecha |
| 5. Auditoría y `GET /auditoria` | Hecha |
| 6. Comando `crear_admin` | Hecha |
| 7. Prueba de permisos que recorre todos los endpoints | Hecha |
| 8. Pantallas | Aplazada a la etapa de frontend |
| 9. Revisión de seguridad y documentación | Hecha |

---

## 8. Pruebas y resultados

Ejecutadas el 2026-10-17 en el entorno de desarrollo de Claude (Linux, Python 3.13,
PostgreSQL 16). **Todavía no se han ejecutado en tu computador.**

| Archivo | Pruebas | Criterios | Resultado |
|---|---|---|---|
| `unit/test_seguridad.py` | 10 | U-06, U-09; configuración de producción | 10 aprobadas |
| `integration/test_autenticacion.py` | 19 | U-01 a U-07, U-09, U-10, U-14, U-16; límite por IP | 19 aprobadas |
| `integration/test_usuarios.py` | 21 | U-12, U-13, U-15, U-17; RU-03, RU-05, RU-09 | 21 aprobadas |
| `integration/test_auditoria.py` | 5 | U-18; filtros por día de Bogotá | 5 aprobadas |
| `integration/test_permisos.py` | 4 | U-11 (todos los endpoints con cada rol y sin sesión) | 4 aprobadas |
| `integration/test_comando_crear_admin.py` | 2 | Creación del primer administrador | 2 aprobadas |
| Pruebas de la fase 7 | 18 | Errores, fechas, salud, migraciones | 18 aprobadas |
| **Total** | **79** | | **79 aprobadas, 0 fallidas** |

`ruff check` y `ruff format --check`: sin hallazgos.

Prueba manual con `curl` contra el servidor real: creación del administrador por consola,
ingreso, `/auth/yo`, rechazo de `POST /usuarios` sin token CSRF, creación con token CSRF y
consulta de la auditoría. Todo respondió como se esperaba.

U-08 (el frontend no guarda el token) se probará con las pantallas; el cliente HTTP de la
fase 7 ya lo cumple y tiene su prueba.

---

## 9. Riesgos, dependencias y documentación

| Riesgo | Mitigación |
|---|---|
| Fuga de la clave de firma JWT | Solo por variable de entorno; la API no arranca con una clave de menos de 32 caracteres ni, en producción, con la de desarrollo |
| La cookie `Secure` no viaja por HTTP | Los navegadores la aceptan en `localhost`; para Postman en tu PC, `APP_COOKIE_SEGURA=false`. En producción no se puede desactivar |
| Bloqueo por intentos usado para bloquear a otro a propósito | El bloqueo dura 15 minutos y el administrador puede restablecer la contraseña, lo que lo levanta |
| El mensaje "cuenta bloqueada" revela que el usuario existe | Solo aparece tras 5 intentos; se aceptó para que un empleado legítimo entienda por qué no entra |
| El límite por IP vive en memoria | Si se despliega con varios procesos, cada uno cuenta aparte; se moverá a la base de datos si hace falta |
| Detrás de un proxy, la IP registrada será la del proxy | Se configurará al preparar el despliegue (fase 10) |
| Quedarse sin administrador | Regla RU-04 con bloqueo de filas y comando `crear_admin` como recuperación |

Dependencias nuevas: `argon2-cffi` y `PyJWT` (aprobadas en la fase 3). Los módulos siguientes
usarán `SesionActual`, `SesionAdministrador` y `auditoria.registrar`.

---

## 10. Lista de verificación de finalización

- [x] Migración 0002 aplicada y reversible
- [x] Criterios U-01 a U-18 cubiertos por pruebas ejecutadas y aprobadas (salvo U-08, que es de frontend)
- [x] Prueba de permisos por rol recorriendo todos los endpoints
- [x] Ruff sin hallazgos
- [x] README con el procedimiento para crear el primer administrador
- [x] Matriz de trazabilidad actualizada
- [ ] Pruebas ejecutadas en el computador de Maryam con su base de datos
- [ ] Aprobación de Maryam

---

## Decisiones tomadas (2026-10-17)

| ID | Pregunta | Decisión de Maryam |
|---|---|---|
| D-1 | ¿Se inicia sesión con correo o con un nombre de usuario? | Nombre de usuario |
| D-2 | ¿El administrador asigna una contraseña temporal a quien la olvida? Añade `POST /usuarios/{id}/restablecer-contrasena` | Sí |
| D-3 | 5 intentos, 15 minutos de bloqueo, 30 minutos de inactividad, 12 horas máximo | Aprobados |
