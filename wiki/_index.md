---
name: _index
type: meta
last_updated: 2026-05-25
---

# Hermes Stack Wiki — Indice

> Wiki personal al estilo Karpathy. El agente mantiene este indice actualizado.
> Ultima actualizacion: 2026-05-25 | Paginas: 36

## Lectura rapida

- **Emergencia:** [[deployment_workflow]] (seccion "Verificar estado previo")
- **Anadir servicio:** [[adding_new_service]]
- **Schema de la wiki:** [[_schema]]

## Entities (10 servicios)

| Nombre | Tipo | Puerto | Dominio | Estado |
|--------|------|--------|---------|--------|
| [[hermes_agent]] | servicio Python | 8080 | hermes.el80.space | active |
| [[litellm_router]] | proxy LLM | 4000 | litellm.el80.space | active |
| [[whisper_stt]] | STT (Whisper) | 9000 | interno | active |
| [[redis]] | cache / session | 6379 | interno | active |
| [[prometheus]] | metricas | 9090 | interno | active |
| [[grafana]] | dashboards | 3000 | grafana.el80.space | active |
| [[caddy]] | reverse proxy + TLS | 80/443 | el80.space | active |
| [[hermes_website]] | frontend Next.js | 3001 | docs.el80.space | active |
| [[filebrowser]] | gestor de archivos | 8095 | files.el80.space | active |
| [[github_actions]] | CI/CD pipeline | N/A (remoto) | github.com | active |
| [[el80_space]] | dominio | N/A | el80.space | active |

## Concepts (13 patrones)

- [[voice_pipeline_e2e]] — flujo de voz E2E: microfono → STT → LLM → TTS → altavoz, SLO <500ms
- [[ci_cd_pipeline]] — GitHub Actions → SSH → git pull → docker compose up → health checks → rollback
- [[docker_compose_stack]] — orquestacion de 10 servicios en VPS unico; distincion servicio vs contenedor
- [[llm_routing]] — LiteLLM como capa de abstraccion sobre OpenRouter y Gemini con fallback automatico
- [[https_git_push]] — patron obligatorio de push con token HTTPS; SSH no funciona en este VPS
- [[nextjs_app_router]] — Next.js 14.2.x con App Router: reglas de version, use client, next.config.mjs
- [[agent_orchestration]] — patron multi-agente: roles, economia de modelos, checkpointing obligatorio
- [[zero_downtime_deploy]] — deployment sin interrupcion: health checks + rollback automatico a HEAD~1
- [[observability_stack]] — Prometheus + Grafana + cadvisor + node-exporter en red monitoring aislada
- [[docker_network_isolation]] — dos redes Docker: backend (funcional) y monitoring (observabilidad)
- [[llm_fallback_strategy]] — politica de fallback OpenRouter → Gemini en LiteLLM
- [[voice_codec_negotiation]] — formato de audio negociado entre cliente, hermes_agent y whisper_stt
- [[hermes_stack_overview]] — arquitectura completa del stack: 10 servicios, SLO <500ms, VPS unico

## Topics (5 guias operativas)

- [[deployment_workflow]] — paso a paso desde git commit hasta verificacion de health checks post-deploy
- [[adding_new_service]] — checklist completo para anadir un nuevo contenedor Docker al stack
- [[frontend_changes]] — workflow para cambios en website/ sin romper el build
- [[ingest_new_source]] — como anadir una nueva fuente de conocimiento a esta wiki (patron Karpathy)
- [[wiki_maintenance]] — lint periodico: paginas huerfanas, referencias rotas, runbooks obsoletos

## Sources (3 fuentes)

- [[2026-05-25_claude_md]] — CLAUDE.md: instrucciones del proyecto, git, Next.js, LaTeX, orquestacion
- [[2026-05-25_memory_files]] — archivos de memoria del agente: perfil, estado del proyecto, feedback
- [[2026-05-25_karpathy_pattern]] — patron Karpathy aplicado a esta wiki: principios y decisiones de diseno

## Estado del conocimiento

- Entidades documentadas: 11 (10 servicios + el80_space)
- Conceptos mapeados: 13
- Guias operativas: 5
- Fuentes ingestadas: 3
- Ultima fuente ingestada: CLAUDE.md + memory files (2026-05-25)
- Referencias rotas resueltas: zero_downtime_deploy, observability_stack, docker_network_isolation, el80_space, llm_fallback_strategy, voice_codec_negotiation, hermes_stack_overview
- Nota: redis_cache en voice_pipeline_e2e.md era alias de [[redis]] — corregido a [[redis]]
