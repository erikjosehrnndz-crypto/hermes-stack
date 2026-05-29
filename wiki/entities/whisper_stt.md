---
name: Whisper STT
type: service
status: active
port: 9000
domain: interno
port_name: whisper-stt
docker_network: backend
health_check_endpoint: GET /health
last_updated: 2026-05-25
---

# Whisper STT

Servicio de reconocimiento de voz (Speech-to-Text) basado en OpenAI Whisper. Convierte audio capturado por micrófono en texto con soporte multiidioma.

## Configuración clave

- **Puerto host:** 127.0.0.1:9000
- **Imagen Docker:** whisper-stt (Python + Whisper)
- **Red Docker:** backend (solo interna)
- **No expuesto públicamente:** Solo [[hermes_agent]] accede
- **Modelos:** Whisper base/small (configurable por tamaño vs latencia)

## Relaciones

- Alimentado por: [[hermes_agent]] (solicitudes de STT)
- Depende de: Audio capturado (micrófono del cliente)
- Alimenta a: [[hermes_agent]] (texto transcrito)
- Implementa: [[voice_pipeline_e2e]]

## Health check

```bash
curl -f http://127.0.0.1:9000/health
```

Respuesta esperada: `{"status": "ok", "model": "base"}` (200)

## Runbook

### Inicio

```bash
docker compose up -d whisper-stt
```

### Restart

```bash
docker compose restart whisper-stt
```

### Logs

```bash
docker compose logs -f whisper-stt
```

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| STT muy lento (>2s) | Latencia de transcripción alta | Reducir model size (small → base), o verificar CPU utilización en host |
| Transcripción pobre | Texto con muchos errores | Verificar calidad de audio de entrada, idioma configurado |
| Container no inicia | Crash inmediato | Verificar espacio en disco (Whisper model ~3GB), logs para OOM |
| Timeout en cliente | Hermes Agent espera respuesta | Aumentar timeout en código de cliente, verificar que STT responda a requests |

## Métricas

- Latencia de transcripción (p50, p95)
- Accuracy (comparar transcripción con referencia si disponible)
- Throughput (transcripciones/min)
- CPU / Memoria

Monitorear en [[prometheus]], visualizar en [[grafana]].

## Referencias

- [[voice_pipeline_e2e]] — primera etapa del pipeline
- [[voice_codec_negotiation]] — negociación de formato de audio
- Dockerfile: `whisper-stt/Dockerfile`
- Modelo: OpenAI Whisper (descargado en build)
