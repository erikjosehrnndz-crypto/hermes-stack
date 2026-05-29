# Reglas — Hermes Agent (Python, performance)

## aiohttp ClientSession — siempre compartida, nunca por request

Crear `aiohttp.ClientSession` en `start()` y cerrarla en `stop()` — **no dentro de `_query_llm`**. `async with aiohttp.ClientSession()` por request abre/cierra TCP+TLS cada vez (~50-200ms overhead).

```python
async def start(self):
    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
    self._session = aiohttp.ClientSession(connector=connector)

async def stop(self):
    if self._session:
        await self._session.close()
```

Registrar en el `aiohttp.web.Application`:
```python
app.on_startup.append(lambda app: app["agent"].start())
app.on_cleanup.append(lambda app: app["agent"].stop())
```

## Handlers externos — usar la sesión compartida del agente

Handlers en módulos separados reciben y usan `agent._session`, no crean `aiohttp.ClientSession()` propia. Patrón: `check_litellm(url, request.app["agent"]._session)` con fallback `async with aiohttp.ClientSession()` solo si `session is None or session.closed`.

## orjson en lugar de json stdlib

`orjson` es drop-in y 3-10× más rápido. Diferencias de API:
- `orjson.dumps()` devuelve `bytes`, no `str`
- Escritura en archivo: `f.write(orjson.dumps(obj) + b"\n")` — modo `"ab"` no `"a"`
- Request HTTP con aiohttp: `data=orjson.dumps(payload)` + `Content-Type: application/json` en headers (no usar `json=`)

## cachetools.TTLCache para dedup de queries de voz

Whisper puede transcribir la misma frase dos veces (eco). `TTLCache(maxsize=256, ttl=60)` con clave `hash(model+text)` previene doble gasto de tokens:

```python
from cachetools import TTLCache
self._query_cache: TTLCache = TTLCache(maxsize=256, ttl=60)
```

## LiteLLM Redis cache — activar desde el inicio

Redis ya corre en el stack. Añadir siempre a `config/litellm.yaml`:

```yaml
litellm_settings:
  cache: True
  cache_params:
    type: redis
    host: redis
    port: 6379
    ttl: 3600
```
