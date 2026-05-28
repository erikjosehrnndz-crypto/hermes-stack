#!/usr/bin/env bash
# Hermes Stack — backup completo del sistema
# Uso: bash /root/scripts/backup.sh
# Destino local: /root/backups/
# Destino remoto: root@104.236.74.0:/root/backups/ (via rsync+SSH)

set -euo pipefail
SHELL=/bin/bash

BACKUP_DIR="/root/backups"
TS=$(date +%Y%m%d-%H%M)
DEST="$BACKUP_DIR/hermes-$TS.tar.gz"
REMOTE_HOST="104.236.74.0"
REMOTE_KEY="/root/.ssh/do_droplet_key"
REMOTE_DIR="/root/backups"

mkdir -p "$BACKUP_DIR"

echo "=== Hermes Backup — $TS ==="

# ─────────────────────────────────────────────────────────────────
# 1. BACKUP DE ARCHIVOS CRÍTICOS
# ─────────────────────────────────────────────────────────────────
echo "→ [1/4] Archivos críticos..."

# Construir lista de rutas que existen
PATHS=()
add_if_exists() {
    [ -e "$1" ] && PATHS+=("$1") || true
}

# Stack raíz
add_if_exists /root/docker-compose.yml
add_if_exists /root/.env
add_if_exists /root/Makefile
add_if_exists /root/AGENTS.md
add_if_exists /root/PENDIENTES.json
add_if_exists /root/PENDIENTES.md
add_if_exists /root/SESSION_HANDOFF.md
add_if_exists /root/ruvector.db
add_if_exists /root/filebrowser.db

# Configuración de servicios
add_if_exists /root/config/

# Hermes Agent — código de personalidades y skills (no en git)
add_if_exists /root/hermes/personalities/
add_if_exists /root/hermes/skills/

# Website — solo la vector DB (el código está en git)
add_if_exists /root/website/ruvector.db

# Docs — PDFs y documentación no regenerable
add_if_exists /root/docs/

# Wiki / knowledge base
add_if_exists /root/wiki/

# Backups previos (incluir 9router_backup con OAuth tokens)
add_if_exists /root/backups/9router_backup

# Agente Hermes (.hermes) — estado, config, DBs
add_if_exists /root/.hermes/state.db
add_if_exists /root/.hermes/state.db-shm
add_if_exists /root/.hermes/state.db-wal
add_if_exists /root/.hermes/state-snapshots/
add_if_exists /root/.hermes/kanban.db
add_if_exists /root/.hermes/kanban.db-shm
add_if_exists /root/.hermes/kanban.db-wal
add_if_exists /root/.hermes/response_store.db
add_if_exists /root/.hermes/response_store.db-shm
add_if_exists /root/.hermes/response_store.db-wal
add_if_exists /root/.hermes/config.yaml
add_if_exists /root/.hermes/auth.json
add_if_exists /root/.hermes/channel_directory.json
add_if_exists /root/.hermes/gateway_state.json
add_if_exists /root/.hermes/processes.json
add_if_exists /root/.hermes/SOUL.md
add_if_exists /root/.hermes/memories/
add_if_exists /root/.hermes/plans/
add_if_exists /root/.hermes/personalities/
add_if_exists /root/.hermes/skills/
add_if_exists /root/.hermes/gateway/
add_if_exists /root/.hermes/cron/
add_if_exists /root/.hermes/hooks/
add_if_exists /root/.hermes/plugins/

# Swarm memory
add_if_exists /root/.swarm/memory.db
add_if_exists /root/.swarm/memory.db-shm
add_if_exists /root/.swarm/memory.db-wal
add_if_exists /root/.swarm/state.json

# Claude Code — memorias persistentes del asistente
add_if_exists /root/.claude/projects/-root/memory/
add_if_exists /root/.claude.json

tar czf "$DEST" \
    --exclude='*/node_modules' \
    --exclude='*/.next' \
    --exclude='*/dist' \
    --exclude='*/__pycache__' \
    --exclude='*.pyc' \
    --exclude='*/logs' \
    --exclude='/root/.hermes/cache' \
    --exclude='/root/.hermes/audio_cache' \
    --exclude='/root/.hermes/image_cache' \
    --exclude='/root/.hermes/lsp' \
    --exclude='/root/.hermes/sessions' \
    --exclude='/root/.hermes/sandboxes' \
    --exclude='/root/.hermes/bin' \
    --exclude='/root/.hermes/models_dev_cache.json' \
    --exclude='/root/.hermes/ollama_cloud_models_cache.json' \
    --exclude='/root/.claude/file-history' \
    --exclude='*.aux' \
    --exclude='*.toc' \
    --exclude='*.out' \
    --exclude='*.lot' \
    --exclude='*.log' \
    --exclude='*.synctex.gz' \
    "${PATHS[@]}"

SIZE=$(du -sh "$DEST" | cut -f1)
echo "   ✓ $DEST ($SIZE)"

# ─────────────────────────────────────────────────────────────────
# 2. BACKUP DE VOLÚMENES DOCKER CRÍTICOS
# ─────────────────────────────────────────────────────────────────
echo "→ [2/4] Volúmenes Docker..."

# Docker Compose en /root genera volúmenes con prefijo "root_"
for vol in root_brain_vault root_brain_lance root_brain_models root_brain_events root_brain_graph root_grafana_data root_litellm_data root_prometheus_data root_couchdb_data; do
    if docker volume inspect "$vol" &>/dev/null; then
        VOL_DEST="$BACKUP_DIR/vol-${vol}-${TS}.tar.gz"
        docker run --rm \
            -v "${vol}:/data:ro" \
            -v "${BACKUP_DIR}:/backup" \
            alpine sh -c "tar czf /backup/vol-${vol}-${TS}.tar.gz /data 2>/dev/null"
        VOL_SIZE=$(du -sh "$VOL_DEST" 2>/dev/null | cut -f1 || echo "?")
        echo "   ✓ vol-${vol} ($VOL_SIZE)"
    else
        echo "   ⏭  vol-${vol} no existe — omitido"
    fi
done

# ─────────────────────────────────────────────────────────────────
# 3. ROTACIÓN: mantener solo los últimos 7 días de backups
# ─────────────────────────────────────────────────────────────────
echo "→ [3/4] Rotación de backups (retención: 7 días)..."

DELETED=0
while IFS= read -r f; do
    rm -f "$f"
    DELETED=$((DELETED + 1))
done < <(find "$BACKUP_DIR" -name "hermes-*.tar.gz" -mtime +7 2>/dev/null || true)
while IFS= read -r f; do
    rm -f "$f"
    DELETED=$((DELETED + 1))
done < <(find "$BACKUP_DIR" -name "vol-*.tar.gz" -mtime +7 2>/dev/null || true)

[ "$DELETED" -gt 0 ] && echo "   ✓ $DELETED backup(s) antiguos eliminados" || echo "   ✓ Sin backups para rotar"

# ─────────────────────────────────────────────────────────────────
# 4. SYNC REMOTO AL DROPLET DO (Control Center)
# ─────────────────────────────────────────────────────────────────
echo "→ [4/4] Sync remoto → $REMOTE_HOST..."

if ssh -i "$REMOTE_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
       root@"$REMOTE_HOST" "mkdir -p $REMOTE_DIR" 2>/dev/null; then
    rsync -az --delete \
        -e "ssh -i $REMOTE_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=15" \
        "$BACKUP_DIR/" \
        "root@$REMOTE_HOST:$REMOTE_DIR/"
    echo "   ✓ Sync a $REMOTE_HOST:$REMOTE_DIR OK"
else
    echo "   ⚠  Droplet no alcanzable — backup local guardado en $BACKUP_DIR"
fi

# ─────────────────────────────────────────────────────────────────
echo ""
echo "✅ Backup completado: $DEST"
echo "   Backups locales disponibles:"
ls -lh "$BACKUP_DIR"/hermes-*.tar.gz 2>/dev/null | awk '{print "     " $5 "  " $9}' || true
