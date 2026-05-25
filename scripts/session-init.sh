#!/usr/bin/env bash
# Protocolo de inicio de sesión — ejecutar al comenzar trabajo

echo "=== Session init — $(date '+%Y-%m-%d %H:%M') ==="

echo ""
echo "→ Git state"
git -C /root status
git -C /root log --oneline -5
git -C /root branch

echo ""
echo "→ Stack state"
docker compose -f /root/docker-compose.yml ps

echo ""
echo "→ Limpiar stale progress bar"
rm -f /tmp/claude_progress && echo "  /tmp/claude_progress limpiado"

echo ""
echo "→ Session handoff pendiente"
if [ -f /root/SESSION_HANDOFF.md ]; then
  echo "  ⚠️  SESSION_HANDOFF.md encontrado — revisar antes de empezar:"
  cat /root/SESSION_HANDOFF.md
else
  echo "  Sin handoff de sesión anterior"
fi

echo ""
echo "→ Tareas activas"
head -40 /root/PENDIENTES.md 2>/dev/null || echo "  PENDIENTES.md no encontrado"

echo ""
echo "=== Inicio listo ==="
