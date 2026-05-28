# SESSION_HANDOFF — 2026-05-28 → próxima sesión

## Objetivo actual
**Brain Phase 2 — Retrieval real**. Reemplazar la búsqueda stub por hybrid (BM25 + dense + RRF + rerank), ingestar la wiki Karpathy existente y dejar `brain_search` devolviendo hits con scores semánticos.

## Estado: Phase 1 (skeleton + MCP vivo) **completada y desplegada**. Phase 2 **pendiente arranque**.

Rama: `main` · Último commit Phase 1: ver `git log --oneline -3` al iniciar.

## Plan canónico (LEER PRIMERO en próxima sesión)
**`/root/.claude/plans/quiero-que-cres-un-humming-journal.md`** — arquitectura completa de 6 fases. **No es opcional**: es el contrato. Cualquier desvío requiere confirmación explícita de Erik.

## Completado esta sesión (Phase 1)
- [x] Skeleton `/root/brain/` con FastAPI 0.115 + FastMCP 3.3 + RQ worker
- [x] `Vault` clase (Markdown + GitPython auto-commit) — escribe `notes/kn-XXXXXXXX.md` con frontmatter compatible wiki Karpathy
- [x] `EventLog` SQLite append-only (schema simplificado tipo OverCR) en `/data/events/events.db`
- [x] `POST /api/v1/ingest/text` (Bearer auth, 202 Accepted, encola job RQ)
- [x] `POST /api/v1/search` stub (filename + body substring, k=5)
- [x] MCP tools: `brain_capture(text, type, tags, title, source)` + `brain_search(q, k)` montados en `/mcp/` HTTP Streamable
- [x] `GET /health` con estado vault/events/redis y count de eventos
- [x] Dockerfile multi-stage slim + Compose `brain` + `brain-worker` con redis-db 2 dedicado
- [x] Caddy `brain.el80.space` con cert Let's Encrypt obtenido (TLS-ALPN-01)
- [x] Acceptance E2E vía HTTPS: nota `kn-9cb63c08` creada, encontrada por `/search`, job procesado por worker, `events.n=2`, MCP `initialize` devuelve `serverInfo: brain v3.3.1` con capabilities tools/resources/prompts
- [x] `BRAIN_API_TOKEN`, `BRAIN_VAULT_PATH`, `BRAIN_EVENTS_PATH`, `BRAIN_REDIS_URL` en `/root/.env`

## Pendiente / no bloqueado
- [ ] **Phase 2: Retrieval real (3-4d)** — LanceDB embedded + BGE-M3 via FastEmbed (ONNX) + late chunking + RRF fusion. Reemplaza `vault.search_by_name` por hybrid pipeline. Incluye `scripts/sync_wiki.py` para ingestar `/root/wiki/**/*.md`.

## Servicios afectados
- **Sin tocar** en Phase 2: hermes-agent, hermes-workspace, litellm-router, whisper-stt, overcr.
- **A modificar** en Phase 2: solo `/root/brain/` (añadir `brain/storage/lance.py`, `brain/pipeline/{chunk,embed,rerank}.py`, dependencias `lancedb`, `fastembed`, `pyarrow`).
- **A añadir** en docker-compose: volumen `brain_lance:/data/lance` en `brain` y `brain-worker`.

## Archivos modificados/creados esta sesión
- `/root/brain/` (nuevo, ~10 archivos Python + Dockerfile + requirements + .gitignore + docker snippets)
- `/root/docker-compose.yml` — añadidos servicios `brain`, `brain-worker` + volúmenes `brain_vault`, `brain_events`
- `/etc/caddy/Caddyfile` — añadido bloque `brain.el80.space` (NO va al repo, vive en VPS)
- `/root/.env` — añadidas `BRAIN_*` (NO va al repo)
- `/root/PENDIENTES.json` + `/root/PENDIENTES.md` — `hs-008` → `phase-1-done`

## Inputs operativos para Phase 2 (zero ambigüedad)

| Recurso | Valor |
|---|---|
| Volumen LanceDB | `brain_lance:/data/lance` (añadir a compose) |
| Modelo embeddings | `BAAI/bge-m3` vía FastEmbed (ONNX, sin GPU) |
| Modelo reranker | `jinaai/jina-reranker-v3-multilingual` (opcional Phase 2, mínimo Phase 4) |
| Estrategia chunking | Late chunking (embed tras contexto completo) |
| Fusion | RRF (Reciprocal Rank Fusion) sobre BM25 + dense |
| Tabla LanceDB principal | `chunks` (cols: chunk_id, node_id, user_id, text, vector[1024], tokens, position, created_at) |
| Tabla LanceDB secundaria | `nodes` (cols: node_id, user_id, type, title, body_path, tags, status, linked_nodes, title_vector, summary, summary_vector) |
| Reindex job | `reindex_node(node_id)` en `brain/workers/jobs/` — sustituye al stub actual |
| Wiki source | `/root/wiki/**/*.md` (34 archivos, frontmatter Karpathy ya compatible) |

### Dependencias Python Phase 2 adicionales
```
lancedb>=0.16.0
pyarrow>=18.0.0
fastembed>=0.4.0
onnxruntime>=1.20.0
tantivy>=0.22.0          # BM25 backend para LanceDB FTS
```

### Test de aceptación Phase 2 (debe pasar al final)
```bash
# Ingestar wiki Karpathy
python /root/brain/scripts/sync_wiki.py            # → ~34 nodos en LanceDB
# Buscar
BRAIN_API_TOKEN=$(grep BRAIN_API_TOKEN /root/.env | cut -d= -f2)
curl -X POST https://brain.el80.space/api/v1/search \
  -H "Authorization: Bearer $BRAIN_API_TOKEN" \
  -d '{"q":"litellm router prometheus","k":5,"mode":"hybrid"}' \
  | jq '.hits[] | {id, score, snippet}'
# Esperado: top-3 contenga entities/litellm_router.md, concepts/voice_pipeline_e2e.md o similar con score > 0.4
```

## Decisiones pendientes (no bloquean Phase 2)
1. **Sparse vectors BGE-M3** — empezar dense puro (1024 dims). Añadir sparse si Phase 2 muestra recall pobre en términos raros.
2. **Reranker en Phase 2 vs 4** — recomendación: dejar para Phase 4 si RRF basta; añadir Jina v3 si los hits top-k no son coherentes.
3. **Mem0 SaaS vs self-hosted** — recomendación: self-hosted en Phase 5.
4. **Telegram bot username, Mailgun cuenta, iOS Shortcuts** — Phase 3.

## Siguiente paso recomendado

Próxima sesión arranca **literalmente así**:

```bash
# 1. Startup (CLAUDE.md checklist)
git status && git log --oneline -5 && docker compose ps brain brain-worker
rm -f /tmp/claude_progress
cat /root/SESSION_HANDOFF.md   # este archivo

# 2. Verificar Phase 1 sigue viva
curl -fsS https://brain.el80.space/health | jq

# 3. Añadir volumen brain_lance al compose + extender requirements.txt con lancedb/fastembed
# 4. Implementar brain/storage/lance.py (open_db, upsert_chunks, search_hybrid)
# 5. Implementar brain/pipeline/{chunk.py,embed.py} con late chunking + BGE-M3 ONNX
# 6. Reescribir brain/workers/jobs/process_node.py → chunk+embed+upsert
# 7. Reescribir brain/api/search.py + brain/mcp/tools.py:brain_search para usar hybrid
# 8. scripts/sync_wiki.py → POST /ingest/text por cada wiki/**/*.md
# 9. Test de aceptación Phase 2 (arriba)
# 10. Commit + actualizar este handoff → Phase 3
```

## Cómo conectar Brain MCP desde Claude Code (instrucción para Erik)

Añadir a `~/.claude/mcp.json` (o configuración equivalente):
```json
{
  "mcpServers": {
    "brain": {
      "type": "http",
      "url": "https://brain.el80.space/mcp/",
      "headers": { "Authorization": "Bearer ${BRAIN_API_TOKEN}" }
    }
  }
}
```
(El token está en `/root/.env` como `BRAIN_API_TOKEN`.)
