# Decisiones técnicas de las fases 3 a 6

Estado: **aprobado por Maryam el 2026-10-17.**
Fecha: 2026-10-17.

Este documento resume cómo se aplican el stack, la arquitectura, el modelo de datos y la
seguridad. No cambia el stack de referencia; solo fija versiones y añade herramientas
auxiliares que el stack necesita para funcionar (marcadas como **Añadido**). La estructura
base de la fase 7 se construyó sobre estas decisiones; si alguna se rechaza, se indica qué
habría que cambiar.

Las reglas de negocio vienen de la propuesta aprobada (RN-01 a RN-31) y no se repiten aquí.

---

## Fase 3. Tecnologías

| Componente | Decisión | Versión fijada | Estado |
|---|---|---|---|
| Lenguaje backend | Python | ≥ 3.12 (probado con 3.13) | Stack de referencia |
| Framework API | FastAPI | 0.143 | Stack de referencia |
| Validación | Pydantic v2 + pydantic-settings para la configuración | 2.14 | Stack de referencia |
| ORM | SQLAlchemy 2.x en modo **síncrono** | 2.1 | Stack de referencia |
| Base de datos | PostgreSQL | 16 | Stack de referencia |
| Driver | psycopg 3 | 3.3 | **Añadido** (necesario para conectar SQLAlchemy a PostgreSQL) |
| Migraciones | Alembic | 1.20 | **Añadido** (versiona el esquema; es la herramienta oficial de SQLAlchemy) |
| Hash de contraseñas | Argon2id (argon2-cffi) | 25.1 | **Añadido** (fase 6) |
| JWT | PyJWT | 2.15 | **Añadido** (fase 6) |
| Pruebas backend | pytest + httpx (cliente de pruebas de FastAPI) | 9.1 | Stack de referencia |
| Calidad backend | ruff (estilo y errores comunes) | 0.17 | **Añadido** |
| Frontend | React + TypeScript con Vite | React 19, TypeScript 6, Vite 8 | Stack de referencia; Vite es **Añadido** como empaquetador |
| Navegación | React Router | 7 | **Añadido** |
| Datos del servidor | TanStack Query | 5 | **Añadido** (caché y reintentos de las consultas a la API) |
| Pruebas frontend | Vitest + Testing Library | Vitest 5 | Stack de referencia |
| Aceptación | Playwright | — | Se instala en la fase 9 |

**Por qué SQLAlchemy síncrono y no asíncrono.** La carga esperada es pequeña (uso interno de
pocos usuarios). El modo síncrono hace más simples y legibles las transacciones financieras
y las pruebas; FastAPI ejecuta los endpoints síncronos en un grupo de hilos sin bloquear el
servidor. Consecuencia: si en el futuro hubiera miles de usuarios simultáneos, habría que
revisar esta decisión.

**Decisiones de librerías que se toman en su módulo (fase 8):** gráficas del tablero
(propuesta: Recharts), generación de PDF (propuesta: WeasyPrint o ReportLab) y Excel
(propuesta: openpyxl). Se presentarán con el módulo correspondiente.

**Proceso diario (RN-10, RN-16, RN-27).** Se implementa como un comando
(`python -m app.tareas.diaria`) que el servidor ejecuta una vez al día con el programador
del sistema (cron o systemd), más el endpoint manual `POST /cobros/generar`. No se usa un
programador dentro del proceso web, porque si el servidor tiene varios procesos el trabajo
se ejecutaría varias veces. Igualmente, cada paso es idempotente.

---

## Fase 4. Arquitectura

- **Monolito modular.** Un solo backend desplegable, dividido por dominios. Es suficiente
  para el alcance del MVP y evita la complejidad de microservicios.
- **Frontend y backend separados** en carpetas `frontend/` y `backend/` del mismo
  repositorio. En producción se sirven **bajo el mismo dominio** (el proxy envía `/api` al
  backend), lo que permite cookies `SameSite=Strict` y evita abrir CORS. En desarrollo, Vite
  hace ese mismo papel de proxy.
- **Capas por dominio** (`backend/app/modulos/<dominio>/`):

  | Archivo | Responsabilidad | Puede depender de |
  |---|---|---|
  | `router.py` | HTTP: rutas, permisos, códigos de estado; **confirma la transacción** (`bd.commit()`) | esquemas, servicio |
  | `esquemas.py` | Entrada y salida (Pydantic) | modelos (enumeraciones) |
  | `servicio.py` | Casos de uso y reglas de negocio; **nunca confirma**, solo `flush()` | esquemas, repositorio, otros servicios |
  | `repositorio.py` | Consultas SQLAlchemy y bloqueos de filas | modelos |
  | `modelos.py` | Tablas (SQLAlchemy) | `app.db` |

  **Unidad de trabajo** (corrección de la revisión): como los servicios no confirman, un caso
  de uso puede pasar por servicios de varios dominios y se guarda todo o nada. Los comandos de
  consola confirman igual que los endpoints.

  **Bloqueos de filas**: cuando una regla depende de varias filas (por ejemplo "siempre queda
  un administrador"), se bloquean primero las filas del conjunto en orden de id y después la
  fila objetivo. Un bloqueo mutuo o fallo de serialización de PostgreSQL responde 409
  `conflicto_concurrente` ("intenta de nuevo"). Este será el patrón de cobros y pagos.

  Las reglas de cálculo puras (fechas de corte, saldos, incrementos) van en funciones sin
  base de datos dentro del servicio o en un `reglas.py`, para probarlas con pruebas unitarias.
- **Dominios:** usuarios, configuración, propietarios, apartaestudios, residentes, bloqueos,
  contratos, incrementos, cobros, pagos, mantenimiento, servicios, tablero e informes,
  auditoría.
- **Errores centralizados.** Toda respuesta de error usa un único formato:
  `{"error": {"codigo": "...", "mensaje": "...", "detalles": [...]}}` con los códigos 401, 403,
  404, 409 (regla de negocio), 422 (datos inválidos) y 500 (sin detalles internos).
- **API** bajo `/api/v1`, documentada con OpenAPI en `/api/docs` (desactivable en producción).

---

## Fase 5. Modelo de datos: convenciones

El modelo entidad-relación detallado de cada tabla se presenta con cada módulo en la fase 8.
Las convenciones generales son:

| Tema | Decisión | Motivo |
|---|---|---|
| Identificadores | `BIGINT` autoincremental | Simple y eficiente. La autorización se valida en el servidor, así que adivinar un id no da acceso |
| Dinero | `NUMERIC(14,0)`, pesos sin decimales | RNF-08: tipo decimal exacto, nunca `float` |
| Porcentajes | `NUMERIC(7,4)` (por ejemplo 4,5000 %) | Exactitud en incrementos |
| Fechas de negocio | `DATE`, calculadas en America/Bogota | RNF-10: el corte y la mora dependen del día en Bogotá |
| Momentos (auditoría, registros) | `TIMESTAMPTZ` guardado en UTC | Evita ambigüedad; se muestran en hora de Bogotá |
| Contratos superpuestos | Restricción de exclusión con `btree_gist` sobre (apartaestudio, rango de fechas) | RN-04 y RN-05 garantizados por la base de datos, no solo por el código |
| Cobros duplicados | Restricción única (contrato, inicio del período) | RN-16, CA-06 |
| Propuestas de incremento | Restricción única (contrato, aniversario) | RN-29, CA-13 |
| Pagos repetidos | Columna de clave de idempotencia única | RNF-07, CA-10 |
| Registros financieros | Sin borrado ni edición; columnas de anulación (fecha, autor, motivo) | RNF-09, RN-24 |
| Auditoría | Tabla de solo inserción; un disparador de PostgreSQL rechaza `UPDATE` y `DELETE` | RF-23: inmodificable incluso ante un error del código |
| Nombres | Tablas y columnas en español, `snake_case`, nombres de restricciones generados por convención | Coherencia con la interfaz y migraciones estables |

---

## Fase 6. Autenticación, autorización y seguridad

| Tema | Decisión |
|---|---|
| Contraseñas | Argon2id con los parámetros recomendados por la librería; mínimo 10 caracteres |
| Sesión | JWT firmado (HS256) en cookie `HttpOnly`, `Secure`, `SameSite=Strict`, ruta `/api` |
| Revocación | Cada JWT lleva un identificador de sesión guardado en la tabla `sesiones`; cerrar sesión, desactivar al usuario o cambiar la contraseña invalida la sesión en el servidor |
| Expiración | 30 minutos de inactividad (se renueva con cada uso) y 12 horas como máximo absoluto |
| CSRF | Token aleatorio por sesión: va en una cookie legible y el frontend lo envía en la cabecera `X-CSRF-Token`; el servidor lo compara con el guardado en la sesión en todo `POST`, `PATCH` y `DELETE` |
| Intentos fallidos | 5 intentos fallidos bloquean el ingreso de esa cuenta durante 15 minutos; el mensaje de error no revela si el usuario existe |
| Autorización | Dependencia de FastAPI por endpoint (`requiere_rol("admin")`); una prueba automática recorre todos los endpoints con cada rol (CA-16) |
| Primer administrador | Se crea con un comando de consola, no por la API |
| Cabeceras | `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy` y `X-Frame-Options` en las respuestas |
| Evidencias | Solo JPG, PNG y PDF, máximo 5 MB, verificados por contenido; guardadas fuera de la base de datos con nombre aleatorio |
| Secretos | Solo por variables de entorno; nunca en el repositorio |
| Configuración | Si falta `APP_ENTORNO`, se asume producción: exige clave JWT propia, cookie segura y cierra `/api/docs` |
| Roles de PostgreSQL | La API usa `apartaestudios_app` (leer, insertar, actualizar; borrar solo sesiones; auditoría solo lectura e inserción). Las migraciones usan el rol dueño |
| HSTS | `Strict-Transport-Security` en producción |
| Auditoría | Usuario, fecha y hora, acción, entidad, valor anterior y nuevo, dirección IP |

**Pendiente de definir antes de producción (no bloquea el desarrollo):** política de
tratamiento de datos personales y retención (Ley 1581), y el proveedor de alojamiento y
respaldos (RNF-15).

---

## Decisiones aprobadas

1. Las herramientas marcadas como **Añadido** (ninguna sustituye al stack de referencia).
2. SQLAlchemy síncrono.
3. Identificadores `BIGINT`.
4. Cookie `SameSite=Strict` con frontend y backend bajo el mismo dominio.
5. Proceso diario como comando programado en el servidor.
