# ============================================================
# Stage 1: Builder — instalar dependencias
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml setup.py ./
RUN pip install --upgrade pip && \
    pip install .

# ============================================================
# Stage 2: Runtime — imagen final mínima
# ============================================================
FROM python:3.11-slim

# Crear usuario no-root
RUN groupadd -r hpd && \
    useradd -r -g hpd -d /app -s /sbin/nologin hpd && \
    mkdir -p /app && \
    chown hpd:hpd /app

WORKDIR /app

# Copiar las dependencias instaladas del builder (system-wide)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el código de la app
COPY --chown=hpd:hpd hpd_cli/ ./hpd_cli/

EXPOSE 3001

# Cambiar a usuario no-root
USER hpd

CMD ["uvicorn", "hpd_cli.api.main:app", "--host", "0.0.0.0", "--port", "3001"]
