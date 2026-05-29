# Reglas — Brain (retrieval pipeline) y MCP

## FastEmbed: verificar modelo disponible antes de codificar

`BAAI/bge-m3` no está en fastembed 0.4.x. Equivalente instalado (1024d, multilingüe): `intfloat/multilingual-e5-large`. Verificar antes de commitear cualquier model_name:

```bash
docker compose exec brain-worker python3 -c \
  "from fastembed import TextEmbedding; [print(m['model']) for m in TextEmbedding.list_supported_models()]"
```

Previene `ValueError: Model X is not supported in TextEmbedding`.

## RRF score ≠ similarity — exponer max(component_scores) como display

RRF = 1/(rrf_k+rank); máximo ≈ 0.016 con rrf_k=60. Usar RRF solo para ordenar hits. El campo `score` devuelto al caller debe ser `max(component_scores.values())` (cosine sim ∈ [0,1]). Previene acceptance tests con `score > 0.4` que fallan aunque el retrieval sea correcto.

## Embedded DBs — acceso multi-proceso

- **Kuzu** ❌ single-proceso — "Could not set lock" si dos procesos abren el mismo archivo
- **SQLite WAL** ✅ multi-proceso — múltiples readers + 1 writer
- **LanceDB** ⚠️ writes single — lecturas concurrentes OK

## fastembed TextCrossEncoder — devuelve floats, no objetos

`TextCrossEncoder.rerank(query, passages)` retorna `list[float]` (logits crudos) en el orden de `passages`. Normalizar con sigmoid: `1.0 / (1.0 + math.exp(-score))`. Previene `AttributeError: 'float' object has no attribute 'document_id'`.

## try/except pass en workers — usar logging mínimo

`except: pass` oculta errores críticos (locks de DB, permisos). Mínimo: `except Exception as e: logging.warning("op failed: %s", e)`.

## FastMCP 3.x — trailing slash obligatorio en URL del cliente

FastMCP 3.x redirige `/mcp` → `/mcp/` (307). Usar siempre `"url": "https://brain.el80.space/mcp/"` (con slash) en `~/.claude.json` y 9router.

## Claude Code — MCP en `~/.claude.json`, no en archivo separado

`mcpServers` vive en `~/.claude.json` (no existe `mcp.json`). Formato HTTP Streamable: `{"type":"http","url":"https://brain.el80.space/mcp/","headers":{"Authorization":"Bearer TOKEN"}}`. Tools aparecen como `mcp__<server>__<tool>`.

## 9router MCP — stdio vs HTTP remoto son mecanismos distintos

- Plugins stdio: `/api/mcp/[plugin]/sse` (ejecuta npx/python3 local).
- HTTP remoto: `PATCH /api/settings {"mcpServers":[{name,url,transport:"http"}]}`. Auth: `POST /api/auth/login` → cookie.
