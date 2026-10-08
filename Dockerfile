# ---------- Etapa 1: instalar las dependencias en un entorno aparte ----------
FROM python:3.11.9-slim-bookworm AS construccion

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


# ---------- Etapa 2: imagen final, solo lo necesario para correr ----------
FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Valores de EJEMPLO, los mismos de .env.example, para que `docker run -p 8000:8000 polizas-api`
# arranque sin más. No son secretos: en un despliegue real se pasan los verdaderos al arrancar
# con `--env-file .env` (o `-e`), que tienen prioridad sobre estos. El .env real nunca entra en
# la imagen: lo excluye .dockerignore.
ENV DATABASE_URL=sqlite:///app.db \
    SECRETO_FIRMA=cambiar-por-un-secreto-largo-y-aleatorio \
    CLAVE_API_REASEGURO=cambiar-por-la-clave-del-reasegurador \
    RUTA_MODELO=modelo.pkl \
    UMBRAL_ALTO_RIESGO=0.6

# Usuario sin privilegios para correr el servicio.
RUN useradd --create-home --uid 1000 aplicacion

WORKDIR /app
COPY --from=construccion /opt/venv /opt/venv
COPY . .
# El usuario puede crear archivos en /app (la base SQLite), pero el código sigue siendo de root.
RUN chown aplicacion:aplicacion /app

USER aplicacion

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)" || exit 1

# Aplica las migraciones y arranca el servicio escuchando hacia fuera del contenedor.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]