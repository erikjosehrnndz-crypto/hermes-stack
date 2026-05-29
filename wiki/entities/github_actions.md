---
name: GitHub Actions
type: service
status: active
port: N/A (CI/CD remote)
domain: N/A
port_name: N/A
docker_network: N/A
health_check_endpoint: N/A
last_updated: 2026-05-25
---

# GitHub Actions

Pipeline de CI/CD remoto. Automáticamente ejecuta tests, builds, y deployments cuando se hace push a ramas o pull requests al repositorio de GitHub.

## Configuración clave

- **Repositorio:** github.com/erikjosehrnndz-crypto/hermes-stack
- **Rama principal:** main
- **Rama de desarrollo:** feat/nextjs-rocket-compat (actualmente activa)
- **Archivo workflow:** `.github/workflows/deploy.yml`
- **Trigger:** push a main, PR a main
- **Destino:** SSH al VPS (/root)
- **Acción final:** `docker compose up -d --build`

## Relaciones

- Monitora: Repository GitHub
- Deploya a: VPS /root (via SSH)
- Interactúa con: [[caddy]], [[hermes_agent]], [[litellm_router]] (health checks)
- Implementa: [[zero_downtime_deploy]]

## Workflow Pipeline

```
1. Git push main branch
   ↓
2. GitHub Actions triggered
   ↓
3. SSH into VPS: /root
   ↓
4. git pull (actualiza código)
   ↓
5. docker compose up -d --build (rebuild + start)
   ↓
6. Health checks (LiteLLM + Hermes Agent)
   ↓
7. [SUCCESS] Deploy completo
   [FAILURE] Rollback automático a HEAD~1
```

## Health checks post-deploy

### LiteLLM (requiere autorización)

```bash
source /root/.env
curl -f -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
```

### Hermes Agent

```bash
curl -f http://127.0.0.1:8080/health
```

**Crítico:** Si ambos health checks fallan, el workflow ejecuta rollback automático a commit anterior.

## Runbook

### Desencadenar manualmente

```bash
# Push a main
git push origin main
# GitHub Actions se ejecuta automáticamente

# O triggear desde GitHub UI
# Actions → workflow → "Run workflow" → Select branch
```

### Ver logs en GitHub

1. Ir a: github.com/erikjosehrnndz-crypto/hermes-stack/actions
2. Click en workflow ejecutándose
3. Expandir pasos para ver logs detallados

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Workflow falla (SSH timeout) | "Could not connect to VPS" | Verificar credenciales SSH en GitHub Secrets, SSH key en /root/.ssh |
| Rollback automático | Deploy "succeeded" pero con warning | Revisar health check logs, uno de los servicios no respondió 200 |
| Build Docker falla | "Error building image" | Ver logs del workflow, ¿build roto en local? Verificar `npm run build` antes de push |
| Git pull falla | "Permission denied" | Revisar permisos en /root/.git, SSH identity en VPS |
| Archivo .env no encontrado | "source: .env not found" | .env debe existir en /root antes de deploy, GitHub Actions asume lo encuentra |

## Cambios recientes (sesión 2026-05-23/24)

- **LiteLLM health check:** Añadido header `Authorization` (requerido)
- **Hermes Agent health check:** Verificado sin header
- **Rollback logic:** HEAD~1 si ambos health checks fallan
- **Instanciación de .env:** Via GitHub Secrets en Actions (si está configurado)

## Restricciones

- **Rama protegida:** main requiere PR review antes de merge (si configurado)
- **SSH key:** Debe estar en GitHub Secrets como variable
- **Credenciales:** LITELLM_MASTER_KEY requerida en .env en VPS

## Referencias

- Workflow file: `.github/workflows/deploy.yml`
- [[zero_downtime_deploy]] — patrón de deployment sin downtime
- [[hermes_agent]] — health check endpoint
- [[litellm_router]] — health check endpoint
- VPS documentación: /root/CLAUDE.md
