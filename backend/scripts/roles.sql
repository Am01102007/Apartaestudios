-- Separa el rol dueño de las tablas (migraciones) del rol con que se conecta la API.
--
-- Ejecútalo UNA vez como superusuario (postgres), conectado a tu base:
--   psql -U postgres -d apartaestudios -v clave_app="CONTRASEÑA_NUEVA" -f scripts/roles.sql
--
-- Luego, en backend/.env:
--   APP_DATABASE_URL=postgresql+psycopg://apartaestudios_app:CONTRASEÑA_NUEVA@localhost:5432/apartaestudios
--   APP_DATABASE_URL_MIGRACIONES=postgresql+psycopg://<dueño actual>:<su contraseña>@localhost:5432/apartaestudios
--
-- Es seguro ejecutarlo de nuevo: no duplica el rol ni los permisos.

\set ON_ERROR_STOP on

SELECT format('CREATE ROLE apartaestudios_app LOGIN PASSWORD %L', :'clave_app')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'apartaestudios_app')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO apartaestudios_app', current_database())
\gexec

GRANT USAGE ON SCHEMA public TO apartaestudios_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO apartaestudios_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO apartaestudios_app;
REVOKE ALL ON alembic_version FROM apartaestudios_app;
GRANT DELETE ON sesiones TO apartaestudios_app;
REVOKE UPDATE, DELETE, TRUNCATE ON auditoria FROM apartaestudios_app;
