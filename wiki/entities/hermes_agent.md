---
name: Hermes Agent
type: service
status: active
port: 8080
domain: hermes.el80.space
port_name: hermes
docker_network: backend
health_check_endpoint: GET /health
last_updated: 2026-05-25
---

# Hermes Agent

Servicio backend conversacional basado en Python que orquesta la inteligencia del Hermes Stack. Procesa entradas de voz/texto, coordina con LiteLLM para múltiples modelos LLM, y genera respuestas sintetizadas por ElevenLabs.

## Configuración clave

- **Puerto host:** 127.0.0.1:8080
- **Imagen Docker:** hermes-agent (Python)
- **Red Docker:** backend
- **Red externa:** Expuesto vía [[caddy]] en hermes.el80.space
- **Dependencias de entorno:** Requiere credenciales de LLM, configuración de [[redis]]

## Relaciones

- Depende de: [[litellm_router]], [[redis]], [[whisper_stt]]
- Alimenta a: [[caddy]], [[prometheus]]
- Comunica con: [[grafana]] (métricas via Prometheus)
- Implementa: [[voice_pipeline_e2e]]

## Health check

```bash
curl -f http://127.0.0.1:8080/health
```

Respuesta esperada: `{"status": "ok"}` (200)

## Runbook

### Inicio

```bash
docker compose up -d hermes
```

### Restart

```bash
docker compose restart hermes
```

### Logs

```bash
docker compose logs -f hermes
```

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| No responde a voz | Whisper STT no conecta | Verificar [[whisper_stt]] está arriba: `docker compose ps whisper-stt` |
| Latencia alta (>500ms) | End-to-end lento | Revisar métricas en [[grafana]]: CPU, latencia LLM, buffer de [[redis]] |
| Crash por OOM | Container killed | Aumentar límites en docker-compose.yml: `mem_limit: 2g` |
| LLM timeout | Respuestas truncadas | Health check [[litellm_router]]: `curl http://127.0.0.1:4000/health` |

## Métricas

- Latencia de procesamiento (p50, p95, p99)
- Throughput (request/min)
- Error rate (timeout, LLM unreachable, malformed input)
- CPU / Memoria

Visualizadas en [[grafana]] dashboard "Hermes Agent".

## Referencias

- [[voice_pipeline_e2e]] — concepto de flujo E2E
- [[hermes_stack_overview]] — arquitectura completa
- Dockerfile: `hermes/Dockerfile`
- health check: `hermes/app/health.py`
