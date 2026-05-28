# SESSION_HANDOFF — 2026-05-28 → próxima sesión

## Objetivo actual
**Brain Phase 4 — 9router MCP integration + wiki expansion**.

## Estado: Phase 3 (Reranker + Graph + Memory) **completada y desplegada**. Phase 4 pendiente.

Rama: `main` · Commits Phase 3: `6d30828` (3a) · `5fa9847` (3b) · `f2c29bc` (3c)

## Plan canónico
**`/root/.claude/plans/quiero-que-cres-un-humming-journal.md`** — arquitectura completa de 6 fases. Contrato no opcional.

## Completado Phase 3 (esta sesión)

### Phase 3a — Reranker (Jina v2 multilingual)
- [x] `fastembed.rerank.cross_encoder.TextCrossEncoder` — `jinaai/jina-reranker-v2-base-multilingual`
- [x] `brain/pipeline/rerank.py`: singleton, scores sigmoid-normalized a [0,1]
- [x] `lance.search_hybrid(..., rerank=True)`: k*3 candidatos RRF → Jina → top-k
- [x] API + MCP: campo `rerank: bool`, mode label `"hybrid+rerank"`
- [x] Acceptance: score separación 3× mayor que hybrid puro

### Phase 3b — Grafo de menciones (SQLite WAL)
- [x] `brain/storage/graph.py`: KuzuGraph impl SQLite WAL — multi-proceso safe
  - Tablas: nodes + edges; upsert_node/delete_node/upsert_mention/expand_1hop
  - Nota: Kuzu descartado (single-proceso); SQLite WAL permite API+worker concurrentes
- [x] `brain/pipeline/extract_mentions.py`: extractor `[[wikilink]]` (pipe/hash support)
- [x] `process_node.py v3`: extrae menciones → graph tras lance upsert (best-effort)
- [x] `lance.search_hybrid_graph()`: hybrid → expand 1-hop → merge scores dampened
- [x] API mode=`"graph"` + MCP `rerank`+`graph`
- [x] docker-compose: volumen `brain_graph:/data/graph`, BRAIN_GRAPH_PATH env var

**Estado grafo:** 32 nodos / 14 aristas (32 wiki files procesadas)

### Phase 3c — Memory layer
- [x] LanceDB tabla `memories` (memory_id, user_id, text, vector, created_at, source)
- [x] `lance.remember/forget/search_memories/count_memories`
- [x] MCP tools: `brain_remember(text)`, `brain_forget(memory_id)`, `brain_search(include_memories=True)`
- [x] API REST: POST /remember, DELETE /remember/{id}, GET /memories
- [x] `brain_search` response incluye `memories: []` cuando hay contexto relevante (threshold=0.65)
- [x] Acceptance: remember → search score=0.86 → forget → memories=0

## Estado del stack Phase 3
```
brain          Up (healthy)  127.0.0.1:8765→8765
brain-worker   Up (healthy)  worker RQ escuchando
LanceDB:       chunks=68, nodes=32, memories=0 (vacío hasta que se usen)
Graph:         32 nodos, 14 aristas
Phase:         3
```

## Pendiente / no bloqueado (Phase 4)

Leer `/root/.claude/plans/quiero-que-cres-un-humming-journal.md` para el detalle de Phase 4+.

### Phase 4 — 9router MCP integration
- Conectar el 9router (puerto 20128) como MCP gateway para brain
- Configurar el cliente Claude Code para usar brain MCP via brain.el80.space

### Phase 5 — Ingesta enriquecida
- Crawl4ai para fuentes externas (papers, docs)
- Procesado periódico via RQ scheduled jobs

### Phase 6 — UI / chat interface
- Widget de memoria en hermes-website (docs.el80.space)
- Historial de búsquedas y memorias del usuario

## Archivos clave Phase 3
- `brain/brain/pipeline/rerank.py` — Jina v2 singleton
- `brain/brain/pipeline/extract_mentions.py` — wikilink extractor
- `brain/brain/storage/graph.py` — KuzuGraph (SQLite WAL impl)
- `brain/brain/storage/lance.py` — LanceStore + memories table
- `brain/brain/mcp/tools.py` — brain_capture/search/remember/forget
- `brain/brain/api/search.py` — REST endpoints incl. /remember

## Decisiones tomadas en Phase 3
1. **Reranker**: `jinaai/jina-reranker-v2-base-multilingual` vía fastembed (ONNX CPU) — disponible en 0.8.0
2. **Scores reranker**: sigmoid(logit) → [0,1] para consistencia con cosine sim
3. **Graph DB**: SQLite WAL en lugar de Kuzu — Kuzu embedded es single-proceso; SQLite WAL soporta API+worker concurrentes
4. **Memory storage**: LanceDB tabla `memories` en lugar de mem0ai — mem0ai requiere LLM para consolidar, sin soporte LanceDB nativo; esta impl es self-contained y sin coste extra por storage

## siguiente paso recomendado

```bash
# 1. Startup
git status && git log --oneline -5 && docker compose ps brain brain-worker
curl -fsS http://127.0.0.1:8765/health | python3 -m json.tool

# 2. Leer plan Phase 4
cat /root/.claude/plans/quiero-que-cres-un-humming-journal.md | grep -A20 "Phase 4"

# 3. Test rápido Phase 3 para confirmar estado
BRAIN_API_TOKEN=$(grep ^BRAIN_API_TOKEN /root/.env | cut -d= -f2)
curl -fsS -X POST http://127.0.0.1:8765/api/v1/search \
  -H "Authorization: Bearer $BRAIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"q":"litellm router prometheus","k":3,"mode":"hybrid","rerank":true}' \
  | python3 -m json.tool
```
