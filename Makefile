SHELL := /bin/bash
# Hermes Stack — harness verification targets
.PHONY: doctor check build-check health-check lint-check status logs clean-tmp

# ─────────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL — un solo comando que verifica todo el stack
# Uso: make doctor
# ─────────────────────────────────────────────────────────────────
doctor:
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║       HERMES STACK — DIAGNÓSTICO COMPLETO   ║"
	@echo "╚══════════════════════════════════════════════╝"
	@echo ""
	@echo "▶ 1/6  REPOSITORIO"
	@BRANCH=$$(git -C /root branch --show-current 2>/dev/null); \
	DIRTY=$$(git -C /root status --porcelain 2>/dev/null | grep -v "^??" | wc -l); \
	AHEAD=$$(git -C /root log --oneline @{u}..HEAD 2>/dev/null | wc -l || echo "?"); \
	echo "   Rama: $$BRANCH   Sin subir: $$AHEAD commit(s)"; \
	if [ "$$DIRTY" -gt 0 ]; then \
	  echo "   ⚠️  $$DIRTY archivo(s) con cambios sin commitear"; \
	else \
	  echo "   ✅  Sin cambios pendientes"; \
	fi
	@echo ""
	@echo "▶ 2/6  SERVICIOS DOCKER"
	@TOTAL=$$(docker compose -f /root/docker-compose.yml ps --format "{{.Service}}" 2>/dev/null | wc -l); \
	RUNNING=$$(docker compose -f /root/docker-compose.yml ps --status running --format "{{.Service}}" 2>/dev/null | wc -l); \
	if [ "$$RUNNING" -eq "$$TOTAL" ] && [ "$$TOTAL" -gt 0 ]; then \
	  echo "   ✅  $$RUNNING/$$TOTAL servicios activos"; \
	else \
	  echo "   ❌  Solo $$RUNNING/$$TOTAL activos — ver: make status"; \
	fi; \
	docker compose -f /root/docker-compose.yml ps --format "   {{.Service}}: {{.Status}}" 2>/dev/null | head -12
	@echo ""
	@echo "▶ 3/6  SALUD DE SERVICIOS"
	@set -a; source /root/.env 2>/dev/null; set +a; \
	if curl -sf http://127.0.0.1:8080/health > /dev/null 2>&1; then \
	  echo "   ✅  Hermes Agent responde"; \
	else \
	  echo "   ❌  Hermes Agent NO responde — ver: make logs"; \
	fi; \
	if curl -sf -H "Authorization: Bearer $$LITELLM_MASTER_KEY" http://127.0.0.1:4000/health > /dev/null 2>&1; then \
	  echo "   ✅  LiteLLM Router responde"; \
	else \
	  echo "   ❌  LiteLLM Router NO responde — ver: make logs"; \
	fi; \
	if curl -sf http://127.0.0.1:3001 > /dev/null 2>&1; then \
	  echo "   ✅  Website responde"; \
	else \
	  echo "   ⚠️  Website no alcanzable en :3001"; \
	fi
	@echo ""
	@echo "▶ 4/6  CALIDAD DE CÓDIGO (Python)"
	@if docker compose -f /root/docker-compose.yml ps hermes 2>/dev/null | grep -q "Up"; then \
	  if docker compose -f /root/docker-compose.yml exec -T hermes sh -c "ruff check /app --exclude .local --quiet && black --check /app --exclude '\.local' --quiet" 2>/dev/null; then \
	    echo "   ✅  Código Python sin errores"; \
	  else \
	    echo "   ⚠️  Hay avisos en el código Python"; \
	  fi; \
	else \
	  echo "   ⏭️  Hermes no activo — saltando lint"; \
	fi
	@echo ""
	@echo "▶ 5/6  HARNESS DEL PROYECTO"
	@for f in /root/AGENTS.md /root/Makefile /root/PENDIENTES.json; do \
	  [ -f "$$f" ] && echo "   ✅  $$(basename $$f)" || echo "   ❌  $$(basename $$f) — FALTA"; \
	done; \
	HANDOFF=/root/SESSION_HANDOFF.md; \
	[ -f "$$HANDOFF" ] && echo "   📋  SESSION_HANDOFF.md pendiente — leer antes de empezar" || true
	@echo ""
	@echo "▶ 6/6  TAREAS PENDIENTES"
	@if [ -f /root/PENDIENTES.md ]; then \
	  grep -E "^(\*\*hs|## )" /root/PENDIENTES.md | head -8 | sed 's/^/   /'; \
	else \
	  echo "   Sin PENDIENTES.md"; \
	fi
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Diagnóstico completo. Busca ❌ para actuar. ║"
	@echo "╚══════════════════════════════════════════════╝"
	@echo ""

check: build-check health-check lint-check
	@echo ""
	@echo "✓  make check complete"

build-check:
	@echo "→ Next.js build"
	cd /root/website && npm run build
	@echo "  build OK"

health-check:
	@echo "→ Health checks"
	@set -a; source /root/.env 2>/dev/null; set +a; \
	curl -sf http://127.0.0.1:8080/health > /dev/null && echo "  hermes OK" || echo "  hermes DOWN"; \
	curl -sf -H "Authorization: Bearer $$LITELLM_MASTER_KEY" http://127.0.0.1:4000/health \
	  > /dev/null && echo "  litellm OK" || echo "  litellm DOWN"

lint-check:
	@echo "→ Python lint"
	@if docker compose ps hermes 2>/dev/null | grep -q "Up"; then \
		docker compose exec -T hermes sh -c "pip install -q ruff black && export PATH=/app/.local/bin:$$PATH && ruff check /app --exclude .local && black --check /app --exclude '\.local'" \
		  2>&1 && echo "  lint OK"; \
	else \
		echo "  hermes not running — skipping lint. Start with: docker compose up -d hermes"; \
	fi

status:
	docker compose ps

logs:
	docker compose logs --tail=40 --no-log-prefix hermes litellm website

clean-tmp:
	@rm -f /tmp/claude_progress 2>/dev/null; \
	rm -f /tmp/harness/*.md 2>/dev/null; \
	echo "  /tmp cleaned"

backup: ## Backup completo del sistema → /root/backups/ + sync a droplet DO
	@bash /root/scripts/backup.sh

backup-list: ## Listar backups disponibles con tamaños
	@echo "Backups locales en /root/backups/:"; \
	ls -lh /root/backups/hermes-*.tar.gz 2>/dev/null | awk '{print "  " $$5 "  " $$9}' || echo "  (ninguno)"; \
	echo "Volúmenes Docker:"; \
	ls -lh /root/backups/vol-*.tar.gz 2>/dev/null | awk '{print "  " $$5 "  " $$9}' || echo "  (ninguno)"
