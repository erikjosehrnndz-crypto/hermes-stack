---
name: LiteLLM Router
type: service
status: active
port: 4000
domain: litellm.el80.space
port_name: litellm
docker_network: backend
health_check_endpoint: GET /health (requiere Authorization header)
last_updated: 2026-05-25
---

# LiteLLM Router

Proxy de orquestación para múltiples proveedores de LLM. Abstrae las diferencias entre OpenRouter y Gemini, proporciona fallback automático, rate limiting, y monitoreo de costos.

## Configuración clave

- **Puerto host:** 127.0.0.1:4000
- **Imagen Docker:** litellm (Python)
- **Red Docker:** backend
- **Red externa:** Expuesto vía [[caddy]] en litellm.el80.space
- **Variable crítica:** `LITELLM_MASTER_KEY` (desde .env)
- **Modelos disponibles:** OpenRouter (fallback), Gemini

## Relaciones

- Alimentado por: [[hermes_agent]]
- Consume: OpenRouter, Gemini (APIs externas)
- Alimenta a: [[caddy]], [[prometheus]]
- Monitorea: [[grafana]]
- Implementa: [[llm_fallback_strategy]]

## Health check

```bash
source /root/.env
curl -f -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
```

**Crítico:** El header `Authorization` es **obligatorio** en este VPS. Sin él, el health check fallará.

Respuesta esperada: `{"status": "ok", "uptime": "..."}` (200)

## Runbook

### Inicio

```bash
docker compose up -d litellm
```

### Restart

```bash
docker compose restart litellm
```

### Logs

```bash
docker compose logs -f litellm
```

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Health check falla (401) | No puede verificar estado | Verificar `LITELLM_MASTER_KEY` en .env, source antes de curl |
| LLM timeout | Respuestas lentas o truncadas | Revisar OpenRouter/Gemini status externos; aumentar timeout en config |
| Rate limit excedido | Error 429 | Verificar costos en OpenRouter, aplicar cuota por modelo |
| Routing fallido (OpenRouter → Gemini) | Siempre cae a Gemini | Revisar log de fallback en docker logs, validar credenciales OpenRouter |

## Métricas

- Latencia por modelo (OpenRouter vs Gemini)
- Error rate y códigos HTTP
- Tasa de fallback (OpenRouter → Gemini)
- Costos acumulados por modelo
- Throughput (tokens/min)

Visualizadas en [[grafana]] dashboard "LiteLLM Usage".

## Referencias

- [[voice_pipeline_e2e]] — dónde encaja en flujo de voz
- [[llm_fallback_strategy]] — política de fallback
- Dockerfile: `litellm/Dockerfile`
- Config: `litellm/config.yaml`
