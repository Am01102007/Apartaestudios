# Módulo 1. Usuarios y sesión

Estado: **diseño propuesto, pendiente de aprobación.** Todavía no hay código de este módulo.
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
- Pantallas: inicio de sesión, cambio de contraseña, lista y formulario de usuarios.

**No incluye**
- Recuperación de contraseña por correo (el MVP no envía correos).
- Autenticación de dos factores.
- Parámetros del sistema e IPC (`/configuracion`, `/ipc`): van con el módulo de incrementos.

---

## 2. Requisitos y criterios de aceptación

| ID | Criterio | Cubre |
|---|---|---|
| U-01 | Con correo y contraseña correctos, `POST /auth/login` responde 200, crea la cookie de sesión `HttpOnly` y la cookie CSRF, y no devuelve el token en el cuerpo | RF-01, RNF-02 |
| U-02 | Con contraseña incorrecta, o con un correo que no existe, la respuesta es la misma: 401 con el mensaje "Correo o contraseña incorrectos" | RF-01 |
| U-03 | Tras 5 intentos fallidos seguidos, la cuenta no puede entrar durante 15 minutos aunque la contraseña sea correcta; pasado ese tiempo sí puede | RF-01 |
| U-04 | Un usuario desactivado no puede iniciar sesión, y sus sesiones abiertas dejan de funcionar de inmediato | RF-02 |
| U-05 | Después de cerrar sesión, la cookie anterior no sirve aunque alguien la haya copiado | RF-01 |
| U-06 | Una sesión sin uso durante 30 minutos expira; ninguna sesión dura más de 12 horas | RNF-02 |
| U-07 | Una petición `POST`, `PATCH` o `DELETE` sin cabecera `X-CSRF-Token` válida se rechaza con 403 | RNF-02, CA-17 |
| U-08 | El frontend no guarda el token ni datos de sesión en `localStorage` ni `sessionStorage` | RNF-02, CA-17 |
| U-09 | La base de datos guarda solo el hash Argon2id de la contraseña; ningún endpoint ni registro devuelve el hash | RNF-01 |
| U-10 | Una contraseña de menos de 10 caracteres o igual al correo se rechaza con 422 | RNF-01 |
| U-11 | Un empleado que llama cualquier endpoint de administrador recibe 403 (prueba automática que recorre todos los endpoints con cada rol) | RNF-03, CA-16 |
| U-12 | No se puede crear un usuario con un correo ya registrado, aunque cambien mayúsculas | RF-02 |
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
| RU-01 | Se inicia sesión con el correo. El correo es único sin distinguir mayúsculas y se guarda en minúsculas |
| RU-02 | Roles: `administrador` y `empleado`. Cada usuario tiene exactamente uno |
| RU-03 | Los usuarios no se eliminan; se desactivan y se reactivan (propuesta aprobada, sección 4) |
| RU-04 | Debe existir siempre al menos un administrador activo |
| RU-05 | Un administrador no puede desactivarse ni cambiarse el rol a sí mismo |
| RU-06 | Contraseña: entre 10 y 128 caracteres, distinta del correo. No se exigen mezclas de símbolos (la longitud protege más y es más fácil de recordar) |
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
| correo | VARCHAR(254) | único (índice sobre `lower(correo)`) |
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
| usuario_id | BIGINT | FK, nulo en intentos de ingreso con correo inexistente |
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
| PATCH | /usuarios/{id} | Admin | Sí | Sí | Edita nombre, correo o rol |
| POST | /usuarios/{id}/desactivar | Admin | Sí | Sí | Desactiva y cierra sus sesiones |
| POST | /usuarios/{id}/activar | Admin | Sí | Sí | Reactiva |
| POST | /usuarios/{id}/restablecer-contrasena | Admin | Sí | Sí | **Nuevo** (D-2): asigna contraseña temporal |
| GET | /auditoria | Admin | No | No | Registro con filtros por usuario, acción, entidad y fechas |

`POST /auth/login` también tiene límite por dirección IP (20 intentos por minuto) para frenar
ataques contra muchas cuentas a la vez.

---

## 6. Archivos que se crearán o modificarán

**Backend (nuevos)**
- `app/core/seguridad.py`: hash Argon2id, firma y lectura de JWT, generación de tokens.
- `app/modulos/usuarios/{modelos,esquemas,repositorio,servicio,router}.py`
- `app/modulos/sesion/{modelos,esquemas,repositorio,servicio,router}.py`
- `app/modulos/sesion/dependencias.py`: `usuario_actual`, `requiere_rol(...)`, verificación CSRF.
- `app/modulos/auditoria/{modelos,esquemas,repositorio,servicio,router}.py`
- `app/comandos/crear_admin.py`: `python -m app.comandos.crear_admin`
- `alembic/versions/0002_usuarios_sesiones_auditoria.py`
- Pruebas en `tests/unit/` y `tests/integration/` (sección 8).

**Backend (modificados)**
- `app/api/router.py`, `app/db/modelos.py`, `pyproject.toml` (argon2-cffi, PyJWT), `.env.example`.
- `app/core/config.py`: clave JWT, cookie segura y tiempos de sesión.

**Frontend (nuevos)**
- `src/sesion/`: contexto de sesión, ruta protegida y ruta solo para administrador.
- `src/paginas/IniciarSesion.tsx`, `CambiarContrasena.tsx`, `usuarios/ListaUsuarios.tsx`, `usuarios/FormularioUsuario.tsx`.
- `src/api/auth.ts`, `src/api/usuarios.ts` y sus pruebas.

**Frontend (modificados)**
- `src/App.tsx` (rutas protegidas) y `src/componentes/Plantilla.tsx` (menú según el rol y botón de salir).

**Documentación**
- Este archivo, el README (crear el primer administrador) y la matriz de trazabilidad.

---

## 7. Implementación por etapas

Cada etapa termina con sus pruebas en verde antes de pasar a la siguiente.

1. Migración 0002 y modelos; prueba de que la auditoría no se puede modificar.
2. Núcleo de seguridad: hash, JWT, tokens; pruebas unitarias.
3. Sesión: login, logout, yo, expiración, bloqueo por intentos, CSRF; dependencias de permisos.
4. Usuarios: CRUD, restablecimiento, reglas RU-04 y RU-05, cierre de sesiones.
5. Auditoría: registro desde los servicios y `GET /auditoria`.
6. Comando `crear_admin`.
7. Prueba que recorre todos los endpoints con cada rol (queda para todos los módulos futuros).
8. Frontend: inicio de sesión, rutas protegidas, cambio de contraseña, gestión de usuarios.
9. Revisión de seguridad del módulo y actualización de la documentación.

---

## 8. Pruebas previstas

Estado: **propuestas, no ejecutadas.**

| Tipo | Qué se prueba | Criterios |
|---|---|---|
| Unitarias | Hash y verificación, rechazo de JWT alterado o vencido, reglas de contraseña, cálculo de expiración | U-06, U-09, U-10 |
| Integración | Login correcto e incorrecto, bloqueo y desbloqueo por tiempo, logout que invalida, desactivación que invalida, último administrador, correo duplicado, cierre de sesiones al cambiar rol o contraseña, auditoría inmodificable | U-01 a U-05, U-12 a U-18 |
| Seguridad | CSRF ausente o incorrecto, cookies con `HttpOnly`/`Secure`/`SameSite=Strict`, recorrido de todos los endpoints con cada rol, sin hash en respuestas | U-07, U-09, U-11 |
| Frontend | Formulario de ingreso, redirección sin sesión, menú según el rol, sin uso de `localStorage` | U-08 |

---

## 9. Riesgos, dependencias y documentación

| Riesgo | Mitigación |
|---|---|
| Fuga de la clave de firma JWT | Solo por variable de entorno; si falta en producción, la API no arranca |
| La cookie `Secure` no viaja por HTTP | Los navegadores la aceptan en `localhost`; en producción se exige HTTPS (RNF-05) |
| Bloqueo por intentos usado para bloquear a otro a propósito | El bloqueo es temporal (15 min) y el administrador puede restablecer |
| Quedarse sin administrador | Regla RU-04 y comando `crear_admin` como recuperación |
| Argon2 consume CPU en cada ingreso | Aceptable para pocos usuarios; los parámetros se pueden ajustar |

Dependencias nuevas: `argon2-cffi` y `PyJWT` (aprobadas en la fase 3). Ningún módulo anterior se
ve afectado; los siguientes módulos usarán `requiere_rol` y el servicio de auditoría.

---

## 10. Lista de verificación de finalización

- [ ] Migración 0002 aplicada y reversible
- [ ] Criterios U-01 a U-18 cubiertos por pruebas ejecutadas y aprobadas
- [ ] Prueba de permisos por rol recorriendo todos los endpoints
- [ ] Ruff, oxlint y compilación sin errores
- [ ] Pantallas probadas en computador y celular
- [ ] README con el procedimiento para crear el primer administrador
- [ ] Matriz de trazabilidad actualizada
- [ ] Aprobación de Maryam

---

## Decisiones que necesito

| ID | Pregunta | Recomendación |
|---|---|---|
| D-1 | ¿Se inicia sesión con correo o con un nombre de usuario? | Correo |
| D-2 | Si un empleado olvida su contraseña, ¿el administrador le asigna una temporal que debe cambiar al entrar? Añade el endpoint `POST /usuarios/{id}/restablecer-contrasena`, que no estaba en la propuesta | Sí |
| D-3 | ¿Los parámetros de 5 intentos, 15 minutos de bloqueo, 30 minutos de inactividad y 12 horas máximo te sirven? | Sí |
