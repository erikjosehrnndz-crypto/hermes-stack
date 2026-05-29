---
name: "Hermes Stack Overview"
type: concept
category: architecture
status: active
introduced_date: "2026-03-01"
last_reviewed: "2026-05-25"
---

# Hermes Stack Overview

El Hermes Stack es una plataforma de IA conversacional autohospedada en un VPS unico bajo el dominio `el80.space`. Integra reconocimiento de voz, razonamiento conversacional con multiples LLMs, sintesis de voz y un frontend web, todo orquestado con Docker Compose.

## Arquitectura de alto nivel

```
[Cliente / Microfono]
    ↓  HTTPS
[[caddy]]  — reverse proxy + TLS (el80.space)
    ↓
[[hermes_agent]] :8080  — orquestador central
    ├── [[whisper_stt]] :9000   — STT local
    ├── [[litellm_router]] :4000 — proxy LLM
    │       ├── OpenRouter (externo)
    │       └── Gemini (externo)
    ├── ElevenLabs Flash v2.5 (externo, WebSocket)
    └── [[redis]] :6379          — sesiones conversacionales
    
[[hermes_website]] :3001  — frontend Next.js
[[grafana]] :3000          — dashboards observabilidad
[[prometheus]] :9090       — metricas (red monitoring)
[[filebrowser]] :8095      — admin de archivos
```

## Servicios activos

10 contenedores Docker orquestados con [[docker_compose_stack]]:

| Categoria | Servicios |
|-----------|-----------|
| Core | [[hermes_agent]], [[litellm_router]], [[whisper_stt]], [[redis]] |
| Frontend | [[hermes_website]] |
| Infraestructura | [[caddy]], [[filebrowser]] |
| Observabilidad | [[prometheus]], [[grafana]], cadvisor, node-exporter |

## Objetivos de diseno

- **SLO de latencia:** < 500ms E2E (voz a voz)
- **Privacidad:** STT local con Whisper (audio no sale del VPS)
- **Resiliencia:** fallback entre proveedores LLM, rollback automatico en deploy
- **Autohospedado:** todo en un VPS unico bajo control total del operador

## Patrones clave

- [[voice_pipeline_e2e]] — flujo completo de audio de entrada a salida
- [[ci_cd_pipeline]] — deployment automatico con rollback
- [[docker_compose_stack]] — orquestacion de todos los servicios
- [[observability_stack]] — Prometheus + Grafana

## Referencias

- [[deployment_workflow]] — como desplegar cambios
- Documento de referencia: `/root/Hermes_Stack_Blueprint.pdf` (52 pp)
