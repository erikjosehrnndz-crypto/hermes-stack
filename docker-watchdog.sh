#!/bin/bash
# docker-watchdog.sh - Script de supervision del daemon Docker
# Monitorea continuamente el estado del motor Docker y sus contenedores principales.
set -u

LOG_FILE="/var/log/docker-watchdog.log"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
STACK_DIR="/root"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Watchdog de Docker y Servicios iniciado."

while true; do
  # 1. Verificar que Docker daemon responde
  if ! docker info > /dev/null 2>&1; then
    log "CRITICO: El demonio de Docker no responde."
    log "Intentando reiniciar servicio docker..."
    
    systemctl restart docker || true
    sleep 30
    
    # Verificar si se recupero
    if docker info > /dev/null 2>&1; then
      log "Docker daemon recuperado exitosamente."
      
      # Intentar restablecer la stack si existe el directorio
      if [ -d "$STACK_DIR" ]; then
        log "Restableciendo contenedores de la stack en $STACK_DIR..."
        cd "$STACK_DIR" && docker compose up -d || log "Error al intentar levantar la stack"
      fi
    else
      log "FALLO CRITICO: Docker daemon no pudo recuperarse."
      # Notificar si hay un webhook configurado
      if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
          --data '{"text":"CRITICO: El demonio de Docker ha fallado en produccion y no responde a reinicios automáticos."}' \
          "$SLACK_WEBHOOK_URL" 2>/dev/null || true
      fi
    fi
  else
    # 2. Verificar contenedores criticos si el daemon esta saludable
    for container in litellm-router hermes-agent whisper-stt; do
      # Comprobamos si el contenedor existe y esta corriendo
      status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "missing")
      if [ "$status" != "running" ]; then
        log "AVISO: El contenedor '$container' no esta activo (estado: $status)"
        
        # En caso de estar caido o faltante, podemos intentar levantarlo si el directorio existe
        if [ -d "$STACK_DIR" ]; then
          log "Intentando levantar/recrear $container..."
          cd "$STACK_DIR" && docker compose up -d --no-deps "$container" || log "Fallo al levantar $container"
        fi
      fi
    done
  fi
  
  sleep 30
done
