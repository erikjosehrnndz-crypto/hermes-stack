---
name: "Zero Downtime Deploy"
type: concept
category: workflow
status: active
introduced_date: "2026-05-01"
last_reviewed: "2026-05-25"
---

# Zero Downtime Deploy

El patron de deployment sin downtime garantiza que los cambios de codigo llegan a produccion sin interrupcion del servicio. En el Hermes Stack se implementa mediante el pipeline de GitHub Actions con health checks y rollback automatico.

## Por que existe

El Hermes Stack es un asistente de voz conversacional en uso activo. Un deployment que interrumpa el servicio es inaceptable durante horas de uso. El patron asegura que si el nuevo codigo no pasa los health checks, el sistema revierte automaticamente al commit anterior.

## Como funciona

El deployment sigue la secuencia:

```
git push main
    ↓
[[github_actions]] — SSH al VPS
    ↓
git pull /root
    ↓
docker compose up -d --build  — rebuild incremental
    ↓
Health checks:
  - curl LiteLLM (con Authorization header)
  - curl Hermes Agent
    ↓ (si falla)
git reset --hard HEAD~1       — rollback al commit anterior
docker compose up -d --build  — re-deploy del commit anterior
```

Caddy mantiene el routing durante el rebuild — los contenedores anteriores siguen sirviendo trafico mientras los nuevos se construyen y arrancan.

## Entidades relacionadas

- [[github_actions]] — ejecutor del pipeline de deploy
- [[caddy]] — mantiene routing durante el rebuild
- [[hermes_agent]] — verificado en health check post-deploy
- [[litellm_router]] — verificado en health check (requiere auth)
- [[ci_cd_pipeline]] — arquitectura completa del pipeline

## Trade-offs

- **Ganado:** rollback automatico ante fallos, historial de deploys en GitHub Actions, sin intervencion manual.
- **Perdido:** no hay entorno de staging — los cambios van directo a produccion. El rollback solo revierte un commit.

## Evolucion

- Se anadio autenticacion al health check de LiteLLM para evitar falsos negativos.
- El path del `git pull` se fijo a `/root` explicitamente.

## Referencias

- [[deployment_workflow]] — guia operativa paso a paso
- [[ci_cd_pipeline]] — arquitectura completa del pipeline
