#!/usr/bin/env bash
# Protocolo de cierre de sesión — ejecutar antes de cerrar el chat

echo "=== Session end — $(date '+%Y-%m-%d %H:%M') ==="

echo ""
echo "→ Git state"
git -C /root status
git -C /root diff --stat

echo ""
echo "→ Cambios sin commitear"
DIRTY=$(git -C /root status --porcelain | wc -l)
if [ "$DIRTY" -gt 0 ]; then
  echo "  ⚠️  $DIRTY cambio(s) sin commitear — commitear antes de cerrar"
else
  echo "  ✓ working tree limpio"
fi

echo ""
echo "→ Health check rápido"
source /root/.env 2>/dev/null
curl -sf http://127.0.0.1:8080/health > /dev/null 2>&1 && echo "  hermes OK" || echo "  hermes DOWN"
curl -sf -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-''}" \
  http://127.0.0.1:4000/health > /dev/null 2>&1 && echo "  litellm OK" || echo "  litellm DOWN"

echo ""
echo "→ TODOs en código"
grep -rn "TODO\|FIXME\|HACK\|XXX" \
  /root/hermes/ /root/website/src/ \
  --include="*.py" --include="*.ts" --include="*.tsx" 2>/dev/null | head -10

echo ""
echo "=== Checklist de cierre ==="
echo "  [ ] Actualizar estado en PENDIENTES.md (añadir evidencia si hay ítem resuelto)"
echo "  [ ] Si hay trabajo incompleto: copiar /root/.claude/templates/session-handoff.md → /root/SESSION_HANDOFF.md y rellenar"
echo "  [ ] Commitear todos los cambios"
echo "  [ ] Anotar próximo paso concreto"
