# Imagen de producción de la API (Clase 1 del Módulo 11, adaptada a uv).
# Las migraciones no corren aquí: las ejecuta el servicio `migrate` de Compose o el
# Pre-deploy Command de Railway.
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Primero las dependencias bloqueadas en uv.lock: esta capa se reutiliza si solo cambia el código.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project \
    && groupadd --system appgroup \
    && useradd --system --gid appgroup --home-dir /app appuser

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000
CMD ["python", "-m", "app.run"]
