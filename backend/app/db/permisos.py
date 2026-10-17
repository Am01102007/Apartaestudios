"""Permisos del rol de PostgreSQL con que se conecta la API (separado del dueño de las tablas).

La API no es dueña de las tablas: no puede cambiar su estructura, desactivar disparadores ni
borrar ni modificar la auditoría. Cada migración que crea tablas termina con
`op.execute(sql_permisos(rol))`; si el rol todavía no existe, no hace nada.
"""

import re

# Tablas en las que la API puede borrar filas (datos temporales, nunca financieros).
TABLAS_CON_BORRADO = ("sesiones",)
# Tablas de solo inserción.
TABLAS_SOLO_INSERCION = ("auditoria",)


def sql_permisos(rol: str) -> str:
    # El rol viene de la configuración, no del usuario; aun así se exige un identificador
    # simple para que no pueda alterar la sentencia.
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", rol):
        raise ValueError(f"Nombre de rol no válido: {rol!r}")
    borrado = "\n".join(f"EXECUTE 'GRANT DELETE ON {t} TO {rol}';" for t in TABLAS_CON_BORRADO)
    solo_insercion = "\n".join(
        f"EXECUTE 'REVOKE UPDATE, DELETE, TRUNCATE ON {t} FROM {rol}';"
        for t in TABLAS_SOLO_INSERCION
    )
    # El rol está validado arriba y los nombres de tabla son constantes.
    return f"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{rol}') THEN
        EXECUTE 'GRANT USAGE ON SCHEMA public TO {rol}';
        EXECUTE 'GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {rol}';
        EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {rol}';
        -- Respaldo: las tablas que cree más adelante el rol que migra quedan con los
        -- mismos permisos aunque una migración olvide llamar a sql_permisos.
        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public
                 GRANT SELECT, INSERT, UPDATE ON TABLES TO {rol}';
        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public
                 GRANT USAGE, SELECT ON SEQUENCES TO {rol}';
        EXECUTE 'REVOKE ALL ON alembic_version FROM {rol}';
        {borrado}
        {solo_insercion}
    END IF;
END
$$;
"""  # noqa: S608
