# Fase 7. Estructura base

Estado: **terminada, pendiente de aprobación.**
Se construyó sobre las decisiones de [decisiones-fases-3-a-6.md](decisiones-fases-3-a-6.md),
también pendientes de aprobación.

## 1. Objetivo y alcance

Dejar listo el esqueleto del repositorio para desarrollar los módulos de la fase 8: proyectos
de backend y frontend que arrancan, se comunican, tienen pruebas y verifican calidad.
No incluye ninguna regla de negocio ni tablas de dominio.

## 2. Qué quedó construido

| Pieza | Ubicación | Propósito |
|---|---|---|
| Fábrica de la aplicación | `backend/app/main.py` | Crea la API, registra errores, cabeceras y rutas; desactiva la documentación en producción |
| Configuración | `backend/app/core/config.py` | Lee variables `APP_*` del entorno o de `.env` |
| Errores centralizados | `backend/app/core/errores.py` | Formato único `{"error": {codigo, mensaje, detalles}}`; 401, 403, 404, 409, 422 y 500 sin detalles internos (RNF-04) |
| Fechas de negocio | `backend/app/core/tiempo.py` | `hoy()` devuelve el día en Bogotá, no el del servidor (RNF-10) |
| Cabeceras de seguridad | `backend/app/core/seguridad_http.py` | CSP, `nosniff`, `X-Frame-Options`, `no-store` |
| Base del modelo | `backend/app/db/base.py` | Convención de nombres, tipo `Dinero` = `NUMERIC(14,0)` (RNF-08), `Porcentaje`, marcas de tiempo en UTC |
| Sesión de base de datos | `backend/app/db/sesion.py` | Una sesión por petición; conexión en UTC |
| Migraciones | `backend/alembic/` | Migración `0001` instala `btree_gist` para la futura restricción de contratos superpuestos |
| Salud | `GET /api/v1/salud` | Indica si la API y la base de datos responden |
| Cliente HTTP | `frontend/src/api/cliente.ts` | Cookie de sesión del navegador, token CSRF en cabecera, conversión de errores; no usa localStorage (RNF-02) |
| Plantilla e inicio | `frontend/src/componentes/`, `frontend/src/paginas/` | Navegación base y página que muestra el estado del servidor |
| Integración continua | `.github/workflows/ci.yml` | Lint, pruebas y compilación; se activa al publicar en GitHub |
| Base de datos local | `docker-compose.yml` | PostgreSQL 16 con la base de pruebas |

## 3. Pruebas y resultados

Ejecutadas el 2026-10-17 en el entorno de desarrollo de Claude (Linux, Python 3.13,
Node 22, PostgreSQL 16). Todavía no se han ejecutado en tu computador.

| Conjunto | Pruebas | Resultado |
|---|---|---|
| Backend unitarias (errores, fechas en Bogotá, cabeceras, documentación en producción, salud sin base de datos) | 14 | 14 aprobadas |
| Backend integración con PostgreSQL (salud real, extensión instalada, migraciones reversibles, conexión en UTC) | 4 | 4 aprobadas |
| Frontend (cliente HTTP con CSRF, errores, sin almacenamiento local; páginas) | 8 | 8 aprobadas |
| `ruff check` y `ruff format --check` | — | Sin hallazgos |
| `oxlint` y compilación TypeScript estricta + `vite build` | — | Sin errores |
| Prueba manual: frontend → proxy → backend → PostgreSQL | 1 | `{"estado":"ok","base_de_datos":"ok"}` |

La integración continua de GitHub está **propuesta, no ejecutada**: no hay repositorio en GitHub.

## 4. Riesgos y pendientes

- La aplicación aún no tiene inicio de sesión: es el primer módulo de la fase 8.
- Falta probar la puesta en marcha en Windows siguiendo el README.
- `starlette` avisa que el cliente de pruebas pasará de `httpx` a `httpx2`; no afecta hoy y
  se resolverá al actualizar dependencias.

## 5. Lista de verificación

- [x] Backend arranca y responde `/api/v1/salud`
- [x] Migraciones aplican y se revierten
- [x] Formato único de errores probado
- [x] Fechas de negocio en hora de Bogotá probadas
- [x] Frontend compila con TypeScript estricto y se comunica con el backend por el proxy
- [x] Cliente sin token en el almacenamiento del navegador
- [ ] Puesta en marcha verificada en el computador de Maryam
- [ ] Aprobación de las decisiones de las fases 3 a 6 y de esta fase

## Siguiente paso propuesto (fase 8)

Módulo 1: usuarios y sesión (RF-01, RF-02, RNF-01, RNF-02, RNF-03), con auditoría básica.
Se presentará con los 10 puntos de entregables por módulo antes de programarlo.
