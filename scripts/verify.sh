#!/usr/bin/env bash
# Verificación integral del Hermes Stack — equivalente de make check como script standalone
set -o pipefail

PASS=0
FAIL=0

ok()   { echo "  ✓ $*"; PASS=$((PASS+1)); }
fail() { echo "  ✗ $*"; FAIL=$((FAIL+1)); }

echo "=== Hermes Stack verify ==="

# 1. Next.js build
echo "→ Next.js build"
if cd /root/website && npm run build --silent 2>&1 | tail -3; then
  ok "Next.js build"
else
  fail "Next.js build — ejecutar: cd website && npm run build"
fi
cd /root

# 2. Docker services
echo "→ Docker services"
source /root/.env 2>/dev/null
RUNNING=$(docker compose ps --status running --format "{{.Service}}" 2>/dev/null | wc -l)
TOTAL=$(docker compose ps --format "{{.Service}}" 2>/dev/null | wc -l)
if [ "$RUNNING" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
  ok "Docker: $RUNNING/$TOTAL servicios running"
else
  fail "Docker: solo $RUNNING/$TOTAL servicios running — run: docker compose ps"
fi

# 3. Hermes health
echo "→ Hermes health"
if curl -sf http://127.0.0.1:8080/health > /dev/null 2>&1; then
  ok "hermes:8080 health"
else
  fail "hermes:8080 no responde — check: docker compose logs hermes"
fi

# 4. LiteLLM health
echo "→ LiteLLM health"
if curl -sf -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" \
     http://127.0.0.1:4000/health > /dev/null 2>&1; then
  ok "litellm:4000 health"
else
  fail "litellm:4000 no responde — check: docker compose logs litellm"
fi

# 5. Git state
echo "→ Git state"
DIRTY=$(git -C /root status --porcelain | wc -l)
if [ "$DIRTY" -eq 0 ]; then
  ok "working tree limpio"
else
  fail "$DIRTY archivo(s) sin commitear — run: git status"
fi

# 6. Orphaned files check
echo "→ Orphaned files"
UNTRACKED=$(git -C /root status --porcelain | grep "^??" | grep -v "backups\|\.db\|snap\|wiki\|docs/" | wc -l)
if [ "$UNTRACKED" -eq 0 ]; then
  ok "sin archivos huérfanos"
else
  fail "$UNTRACKED archivo(s) untracked — run: git status"
fi

echo ""
echo "=== Resultado: $PASS OK, $FAIL FAIL ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
