# Dockerfile - Contenedor del agente con hardening de seguridad
FROM python:3.12-slim

# Crear usuario no-root con UID/GID fijos
RUN groupadd -g 5000 hermesgrp && \
    useradd -u 5000 -g hermesgrp -s /bin/bash -m hermes

# Instalar dependencias del sistema indispensables
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo con permisos correctos
WORKDIR /app
RUN chown hermes:hermesgrp /app

# Copiar dependencias e instalar
COPY --chown=hermes:hermesgrp requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo de la aplicacion
COPY --chown=hermes:hermesgrp . .

# Crear directorios necesarios con permisos correspondientes
RUN mkdir -p /app/logs /app/data /app/tmp /app/skills && \
    chown -R hermes:hermesgrp /app

# Variables de entorno de Python y temporales
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    TMPDIR=/app/tmp \
    HOME=/app \
    PYTHONPATH=/app

# Healthcheck: verificar que el agente responde correctamente
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Cambiar a usuario no-root
USER hermes:hermesgrp

# Puerto de la aplicacion (no privilegiado)
EXPOSE 8080

# Comando de inicio
CMD ["python", "main.py"]
