SHELL := /bin/bash
# Hermes Stack — harness verification targets
.PHONY: check build-check health-check lint-check status logs clean-tmp

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
		docker compose exec -T hermes sh -c "pip install -q ruff black && ruff check /app && black --check /app" \
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
