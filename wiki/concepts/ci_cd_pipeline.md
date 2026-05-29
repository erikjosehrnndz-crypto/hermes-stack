---
name: "CI/CD Pipeline"
type: "concept"
category: "workflow"
status: "active"
introduced_date: "2026-05-01"
last_reviewed: "2026-05-25"
---

# CI/CD Pipeline

El pipeline de integración y despliegue continuo automatiza la entrega de cambios desde el repositorio GitHub hasta el VPS de producción, con verificación de salud y rollback automático en caso de fallo.

## Por qué existe

El Hermes Stack corre en un VPS único. Actualizar servicios manualmente requeriría acceso SSH al servidor en cada cambio. El pipeline elimina este paso: un `git push` a `main` dispara automáticamente la actualización del stack en producción, con rollback automático si los health checks fallan.

## Cómo funciona

Flujo completo desde push hasta producción:

```
Developer → git push origin main
    ↓
[[github_actions]]  — trigger: push a main
    ↓  (SSH al VPS)
VPS /root
    ↓
git pull /root    — actualiza código
    ↓
docker compose up -d --build   — reconstruye y levanta servicios
    ↓
Health checks autenticados:
  - curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
  - curl -f http://127.0.0.1:8080/health
    ↓ (si falla)
git reset --hard HEAD~1        — rollback automático al commit anterior
docker compose up -d --build   — re-deploy del commit anterior
```

Pasos detallados:

1. **Trigger:** Push o merge a la rama `main` en GitHub.
2. **GitHub Actions:** El workflow `.github/workflows/deploy.yml` se ejecuta en el runner de GitHub.
3. **SSH al VPS:** El runner se conecta vía SSH al servidor en `/root`.
4. **Git pull:** Se actualiza el código local con los cambios del commit nuevo.
5. **Docker rebuild:** `docker compose up -d --build` reconstruye las imágenes afectadas y levanta los contenedores.
6. **Health checks:** Se verifica que `litellm-router` y `hermes-agent` respondan correctamente. LiteLLM requiere header de autenticación con `LITELLM_MASTER_KEY`.
7. **Rollback:** Si cualquier health check falla, se hace `git reset --hard HEAD~1` y se re-despliega el commit anterior automáticamente.

## Entidades relacionadas

- [[github_actions]] — ejecutor del workflow de deploy
- [[hermes_agent]] — uno de los servicios verificados en health check
- [[litellm_router]] — el otro servicio verificado, requiere auth
- [[docker_compose_stack]] — cómo se orquesta el rebuild
- [[el80_space]] — dominio del VPS destino

## Trade-offs

- **Ganado:** despliegue sin intervención manual, rollback automático ante fallos, historial de deploys en GitHub Actions.
- **Perdido:** dependencia total en SSH al VPS; si el VPS no es alcanzable, el pipeline falla. No hay entorno de staging: los cambios van directo a producción.

## Evolución

- Se añadió autenticación al health check de LiteLLM (antes era unauthenticated, lo que causaba falsos negativos).
- Se corrigió `setup-caddy.sh` para incluir `docs.el80.space` y email en el bloque global de Caddy.
- El path del `git pull` se fijó a `/root` explícitamente para evitar ambigüedades.

## Referencias

- [[deployment_workflow]] — guía operativa paso a paso para hacer un deploy
- [[https_git_push]] — cómo hacer push con token desde el VPS
- `.github/workflows/deploy.yml` — leer antes de modificar el workflow
