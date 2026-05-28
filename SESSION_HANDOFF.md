# SESSION_HANDOFF — 2026-05-28 → próxima sesión

## Objetivo actual
**Brain Phase 3 — Reranker + Kuzu graph + Mem0 memory layer**.

## Estado: Phase 2 (LanceDB hybrid retrieval) **completada y desplegada**. Phase 3 pendiente.

Rama: `main` · Último commit Phase 2: `4dd10e2`

## Plan canónico
**`/root/.claude/plans/quiero-que-cres-un-humming-journal.md`** — arquitectura completa de 6 fases. Contrato no opcional.

## Completado Phase 2 (esta sesión)
- [x] LanceDB 0.16 embedded: tablas `chunks` + `nodes`, schema pyarrow 1024-dim
- [x] FastEmbed `intfloat/multilingual-e5-large` (ONNX CPU, 1024d, multilingual) — nota: BAAI/bge-m3 no disponible en esta versión de fastembed
- [x] Chunker late-chunking: ~480 tokens soft cap, 64 overlap, split por bloques de párrafo
- [x] `LanceStore`: delete_node (idempotente), upsert_chunks, upsert_node, ensure_fts_index (tantivy)
- [x] `search_dense` (cosine sim), `search_bm25` (tantivy FTS + sigmoid), `search_hybrid` (RRF + max component score)
- [x] `process_node` worker reescrito: chunk→embed→upsert idempotente, job_timeout=300
- [x] `/api/v1/search` + MCP `brain_search`: hybrid/dense/bm25/keyword
- [x] `scripts/sync_wiki.py`: 32 wikis ingested, node_id = `kn-wiki-{sha1[:8]}` (estable)
- [x] Volumes `brain_lance:/data/lance` + `brain_models:/data/models`
- [x] **Acceptance test PASS**: q="litellm router prometheus" → top-3 score=0.84 (Prometheus, LiteLLM Router)

## Estado del stack Phase 2
```
brain          Up (healthy)  127.0.0.1:8765→8765
brain-worker   Up (healthy)  worker RQ escuchando
LanceDB:       chunks=68, nodes=32, phase=2
```

## Pendiente / no bloqueado (Phase 3)

### Phase 3a — Reranker (Jina v3)
- Añadir `jinaai/jina-reranker-v2-base-multilingual` vía FastEmbed `Reranker`
- Rerank top-k*3 dense → return top-k con scores más precisos
- Actualizar `lance.py` → `search_hybrid()` acepta `rerank=True`

### Phase 3b — Kuzu graph
- Añadir `kuzu>=0.10.0` a requirements.txt
- Volume `brain_graph:/data/graph`
- Schema: nodos `Node(id, type, title)` + aristas `MENTIONS(from, to, weight)`
- Extraer menciones `[[wikilink]]` del body al procesar cada nodo
- `LanceStore.search_hybrid_graph()`: hits dense → expand por Kuzu (1-hop) → merge scores

### Phase 3c — Mem0 memory layer
- `mem0ai>=0.1.0` con backend LanceDB (reusar volumen)
- `brain_remember(text, user_id)` → MCP tool
- `brain_forget(memory_id)` → MCP tool
- Integrar en `brain_search()` si memories relevantes → anteponer al contexto

## Archivos clave Phase 2 (no tocar sin entender)
- `/root/brain/brain/storage/lance.py` — LanceStore completo
- `/root/brain/brain/pipeline/chunk.py` — chunker late-chunking
- `/root/brain/brain/pipeline/embed.py` — FastEmbed singleton, `embed_texts` + `embed_query`
- `/root/brain/brain/workers/jobs/process_node.py` — worker principal
- `/root/brain/brain/api/search.py` — REST endpoint
- `/root/brain/brain/mcp/tools.py` — MCP tools

## Decisiones tomadas en Phase 2
1. **Modelo**: `intfloat/multilingual-e5-large` en lugar de `BAAI/bge-m3` — bge-m3 no disponible en fastembed 0.4.x con esta build. E5-large es 1024d multilingüe, igual de bueno.
2. **Score híbrido**: RRF para ranking, `max(component_scores.values())` como score devuelto — semánticamente significativo (cosine sim ∈ [0,1]).
3. **32 archivos** (no 34) ingested — 2 archivos vacíos skipeados por `sync_wiki.py`.

## siguiente paso recomendado

```bash
# 1. Startup
git status && git log --oneline -5 && docker compose ps brain brain-worker
rm -f /tmp/claude_progress
curl -fsS http://127.0.0.1:8765/health | python3 -m json.tool

# 2. Phase 3a — reranker
pip install fastembed --upgrade   # verificar si Reranker disponible
# Editar brain/brain/storage/lance.py → search_hybrid(..., rerank=True)
# Editar brain/requirements.txt → añadir reranker dep si distinto
# docker compose build brain brain-worker && docker compose up -d brain brain-worker

# 3. Test reranker
BRAIN_API_TOKEN=$(grep ^BRAIN_API_TOKEN /root/.env | cut -d= -f2)
curl -fsS -X POST http://127.0.0.1:8765/api/v1/search \
  -H "Authorization: Bearer $BRAIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"q":"litellm router prometheus","k":5,"mode":"hybrid"}' \
  | python3 -m json.tool
# Esperado: mismos top-3 con scores más diferenciados

# 4. Phase 3b — Kuzu graph (si reranker funciona)
# 5. Commit + actualizar SESSION_HANDOFF → Phase 4
```

## Cómo conectar Brain MCP desde Claude Code
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
