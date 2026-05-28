# SESSION_HANDOFF — 2026-05-28 → próxima sesión

## Objetivo actual
Construir **Brain** — segundo cerebro PKM (journal + knowledge base + memoria conversacional) integrado al Hermes Stack. Plan completo de 6 fases ya aprobado por Erik.

## Estado: Phase 0 (research + arquitectura) **completada**. Phase 1 (skeleton + MCP vivo) **pendiente arranque**.

Rama: `main` · Último commit: ver `git log -1` al iniciar

## Plan canónico (LEER PRIMERO en próxima sesión)
**`/root/.claude/plans/quiero-que-cres-un-humming-journal.md`** — arquitectura completa, stack, modelo de datos, 12 endpoints REST, 7 tools MCP, 8 surfaces de captura, 6 fases, estructura del repo, variables `.env`, tests de aceptación. **No es opcional**: es el contrato. Cualquier desvío de ese plan requiere confirmación explícita de Erik.

## Completado esta sesión (Phase 0)
- [x] Conversación con Erik para clarificar alcance (3 preguntas con AskUserQuestion) — decisiones: tres capas integradas, API headless con MCP primario, single-user con `user_id` desde el inicio
- [x] Research SOTA mayo 2026 (4 agentes Explore en paralelo) — Mem0, LightRAG, GraphRAG, MCP HTTP Streamable, BGE-M3, Jina-reranker-v3, LanceDB, Kuzu, FastEmbed, Instructor, Langfuse, late chunking
- [x] Re-mapeo profundo del stack existente — OverCR memory layer completo (`MemoryRecord`, `MemoryManager`, schemas), wiki Karpathy schema (`_schema.md`, 34 archivos), Caddy routing (7 subdominios), voice pipeline (`/root/hermes/voice/`), LiteLLM config (sin embeddings), modelos disponibles
- [x] Arquitectura definitiva diseñada (v2 Opus 4.7) — 5 principios, stack tabla por capa, diagrama ASCII completo, pipeline background, capas de captura, plan de fases
- [x] Plan escrito en `/root/.claude/plans/quiero-que-cres-un-humming-journal.md` — aprobado por Erik vía ExitPlanMode
- [x] `PENDIENTES.json` + `PENDIENTES.md` — entrada `hs-008` añadida con verification cmd

## Pendiente / no bloqueado
- [ ] **Phase 1: Skeleton + MCP vivo** — crear `/root/brain/`, FastAPI + FastMCP en `:8765`, `vault/` git-inicializado, endpoints `GET /health` + `POST /ingest/text`, MCP tools stub `brain_capture` + `brain_search`. Estimado 1-2 días.

## Servicios afectados
- **Sin tocar** en Phase 1: hermes-agent, hermes-workspace, litellm-router, whisper-stt, overcr.
- **A añadir** en Phase 1: dos servicios nuevos en `docker-compose.yml` (`brain`, `brain-worker`) + un bloque en Caddy.

## Archivos modificados esta sesión
- `/root/.claude/plans/quiero-que-cres-un-humming-journal.md` — creado (plan completo, ignorado por git pero persistente en disco)
- `/root/PENDIENTES.json` — añadida entrada `hs-008`
- `/root/PENDIENTES.md` — añadida fila `hs-008`

## Inputs operativos para Phase 1 (zero ambigüedad)

| Recurso | Valor |
|---|---|
| Puerto API | `127.0.0.1:8765:8765` |
| Puerto worker | sin exponer |
| Caddy subdomain | `brain.el80.space` (copiar bloque de `docs.el80.space` y adaptar) |
| Network Docker | `backend` |
| Volúmenes | `brain_vault:/data/vault`, `brain_lance:/data/lance`, `brain_kuzu:/data/kuzu`, `brain_events:/data/events` |
| Health endpoint | `GET /health` |
| Auth | Bearer token `BRAIN_API_TOKEN` (generar uno nuevo con `openssl rand -hex 32` y añadirlo a `/root/.env`) |
| Reutilizar | `/root/integrations/overcr/memory/` (importar `MemoryRecord` para audit/lifecycle) · `/root/wiki/_schema.md` (frontmatter compatible) |

### Dependencias Python Phase 1 mínimas
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
fastmcp>=2.0.0
pydantic>=2.7.0
pydantic-settings>=2.4.0
python-frontmatter>=1.1.0
gitpython>=3.1.43
rq>=2.0.0
redis>=5.0.0
```

### Test de aceptación Phase 1 (debe pasar al final)
```bash
curl -f http://localhost:8765/health
BRAIN_API_TOKEN=$(grep BRAIN_API_TOKEN /root/.env | cut -d= -f2)
curl -X POST http://localhost:8765/api/v1/ingest/text \
  -H "Authorization: Bearer $BRAIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"primera prueba","tags":["test"]}'
ls /data/vault/notes/                            # → kn-XXXXXXXX.md
git -C /data/vault log --oneline                 # → al menos 1 commit
```

Y conectar MCP desde Claude Code:
```json
{"mcpServers": {"brain": {"type": "http", "url": "https://brain.el80.space/mcp",
  "headers": {"Authorization": "Bearer ${BRAIN_API_TOKEN}"}}}}
```

## Decisiones aún por confirmar (no bloquean Phase 1)
1. **Mem0** SaaS vs self-hosted — recomendación: self-hosted en Phase 5
2. **Telegram bot username** — Erik elige con @BotFather en Phase 3
3. **Mailgun cuenta** — Erik verifica en Phase 3
4. **iOS Shortcuts** — plantilla descargable al cerrar Phase 3
5. **Embeddings dims** — empezar dense puro (1024 BGE-M3), añadir sparse si Phase 2 lo necesita

## Siguiente paso recomendado

Próxima sesión arranca **literalmente así**:

```bash
# 1. Startup (CLAUDE.md checklist)
git status && git log --oneline -5 && docker compose ps
rm -f /tmp/claude_progress
cat /root/SESSION_HANDOFF.md

# 2. Leer plan canónico
cat /root/.claude/plans/quiero-que-cres-un-humming-journal.md

# 3. Verificar puerto 8765 libre + token .env
ss -tlnp | grep 8765 || echo "puerto libre"
grep -q BRAIN_API_TOKEN /root/.env || echo "BRAIN_API_TOKEN=$(openssl rand -hex 32)" >> /root/.env

# 4. Crear /root/brain/ siguiendo §"Estructura del repo" + §"Handoff para Phase 1" del plan
# 5. docker compose up -d --build brain brain-worker
# 6. Ejecutar test de aceptación Phase 1
# 7. git commit; actualizar este handoff (estado → Phase 2 pendiente) o borrar si Brain Phase 1 done
```

## Startup para retomar
```bash
git status && git log --oneline -3
docker compose ps
cat /root/.claude/plans/quiero-que-cres-un-humming-journal.md   # plan completo
# Continuar desde: Phase 1 — crear /root/brain/ con skeleton FastAPI + FastMCP + vault git
```
