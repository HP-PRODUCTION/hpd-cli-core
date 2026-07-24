# ============================================================
# Stage 1: Builder — instalar dependencias
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Dependencias del sistema para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# ============================================================
# Stage 2: Runtime — imagen final mínima
# ============================================================
FROM python:3.11-slim

# Instalar runtime deps del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root y estructura de directorios
RUN groupadd -r hpd && \
    useradd -r -g hpd -d /app -s /sbin/nologin hpd && \
    mkdir -p /app /app/data /app/hpd_cli /home/hpd/.hpd && \
    chown -R hpd:hpd /app /home/hpd/.hpd

WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código de la app y UI pre-construida
COPY --chown=hpd:hpd hpd_cli/ ./hpd_cli/
COPY --chown=hpd:hpd control-plane/dist ./control-plane/dist/

# Volumen para datos persistentes
VOLUME ["/home/hpd/.hpd", "/app/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:3100/api/v1/system/health || exit 1

EXPOSE 3100

# Cambiar a usuario no-root
USER hpd

ENV HPD_DATABASE_URL="sqlite:////home/hpd/.hpd/hpd.db"
ENV RATE_LIMIT_WINDOW_SECONDS=60
ENV RATE_LIMIT_MAX_REQUESTS=30

CMD ["uvicorn", "hpd_cli.api.main:app", "--host", "0.0.0.0", "--port", "3100"]
