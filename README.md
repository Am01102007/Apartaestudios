# Sistema de administración de apartaestudios

Aplicación web interna para administrar apartaestudios, residentes, contratos, cobros,
pagos, cartera, mantenimiento y servicios públicos. Opera en pesos colombianos y en la zona
horaria de Bogotá.

- Propuesta aprobada y reglas de negocio: `Propuesta-sistema-apartaestudios.pdf`
  (archivos del proyecto).
- Decisiones técnicas: [docs/decisiones-fases-3-a-6.md](docs/decisiones-fases-3-a-6.md).
- Módulos: [docs/modulos/](docs/modulos/). Trazabilidad: [docs/trazabilidad.md](docs/trazabilidad.md).

## Estructura

```
backend/            API REST (Python, FastAPI, SQLAlchemy, PostgreSQL)
  app/
    core/           Configuración, errores, fechas en hora de Bogotá, cabeceras de seguridad
    db/             Base del modelo, convenciones y sesión de base de datos
    api/            Router /api/v1 y verificación de salud
    modulos/        Un paquete por dominio: usuarios, auditoria, inmuebles
  alembic/          Migraciones de la base de datos
  tests/            unit/ (sin base de datos) e integration/ (PostgreSQL real)
frontend/           Interfaz web (React, TypeScript, Vite)
  src/api/          Cliente HTTP (cookie de sesión, token CSRF, errores)
  src/componentes/  Componentes comunes
  src/paginas/      Páginas
docs/               Decisiones y documentación por fase
```

## Requisitos

- [uv](https://docs.astral.sh/uv/) (instala y gestiona Python 3.12+ y las dependencias)
- Node.js 22 o superior
- PostgreSQL 16 (instalado, o con Docker Desktop usando `docker compose up -d`)

## Puesta en marcha en Windows (PowerShell)

### 1. Base de datos

Con Docker Desktop:

```powershell
docker compose up -d
```

Con PostgreSQL instalado, desde `psql` como superusuario:

```sql
CREATE ROLE apartaestudios LOGIN PASSWORD 'apartaestudios';
CREATE DATABASE apartaestudios OWNER apartaestudios;
CREATE DATABASE apartaestudios_test OWNER apartaestudios;
```

### 2. Backend

```powershell
cd backend
uv sync                          # crea .venv e instala todo según uv.lock
Copy-Item .env.example .env      # luego edita .env con los datos de tu base de datos
uv run alembic upgrade head
uv run python -m app.comandos.crear_admin --usuario TU_USUARIO --nombre "Tu nombre"
uv run uvicorn app.main:app --reload
```

Para añadir una dependencia: `uv add paquete` (o `uv add --dev paquete` para pruebas).

### 3. Rol de la aplicación (recomendado)

Así la API no se conecta como dueña de las tablas y no puede desactivar la protección de la
auditoría. Una sola vez, como superusuario de PostgreSQL y desde `backend`:

```powershell
psql -U postgres -d apartaestudios -v clave_app="UNA_CONTRASEÑA_NUEVA" -f scripts/roles.sql
```

Después, en `.env`, la API usa el rol nuevo y las migraciones siguen con el dueño:

```
APP_DATABASE_URL=postgresql+psycopg://apartaestudios_app:UNA_CONTRASEÑA_NUEVA@localhost:5432/apartaestudios
APP_DATABASE_URL_MIGRACIONES=postgresql+psycopg://apartaestudios:apartaestudios@localhost:5432/apartaestudios
```

Las migraciones nuevas otorgan sus permisos a ese rol automáticamente.

### Mantenimiento

`uv run python -m app.comandos.purgar_sesiones` borra las sesiones cerradas o vencidas hace
más de 90 días (`--dias N` para cambiarlo). Conviene programarlo semanalmente.

`crear_admin` pide la contraseña sin mostrarla (mínimo 10 caracteres). Solo se usa para el
primer administrador o para recuperar el acceso; los demás usuarios los crea un administrador
desde la API.

La API queda en http://localhost:8000 y su documentación en http://localhost:8000/api/docs.

**Probar la API desde /api/docs.** Ejecuta `POST /auth/login`; el navegador guarda la sesión.
En las operaciones `POST`, `PATCH` y `DELETE` escribe en el campo `X-CSRF-Token` el valor de
la cookie `csrf_token` (en el navegador: F12 → Aplicación → Cookies).

### 4. Frontend

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

La aplicación queda en http://localhost:5173. Vite reenvía `/api` al backend.

En macOS o Linux los comandos son los mismos, salvo `cp .env.example .env`.

## Pruebas y calidad

```powershell
# Backend (desde backend/)
uv run pytest                       # unitarias e integración (necesita la base apartaestudios_test)
uv run pytest -m "not integracion"  # solo unitarias, sin base de datos
uv run ruff check .
uv run ruff format --check .

# Frontend (desde frontend/)
npm test
npm run lint
npm run build
```

Las pruebas de integración borran y recrean el esquema de la base indicada en
`APP_DATABASE_URL_PRUEBAS`, y se niegan a ejecutarse si su nombre no termina en `_test`.
