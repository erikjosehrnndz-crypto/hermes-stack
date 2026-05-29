---
name: "Deployment Workflow"
type: "topic"
difficulty: "intermediate"
time_estimate: "5-10 min"
involves: ["github_actions", "hermes_agent", "litellm_router", "docker_compose_stack", "ci_cd_pipeline"]
last_updated: "2026-05-25"
---

# Deployment Workflow

En una línea: cómo llevar un cambio de código desde el editor hasta producción en `el80.space`.

## Por qué importa

El Hermes Stack tiene rollback automático, pero un deploy mal ejecutado puede causar downtime momentáneo. Seguir este workflow garantiza que los cambios lleguen a producción de forma verificada.

## Pasos

### 1. Verificar estado previo

```bash
git status                    # cambios sin commitear
git log --oneline -5          # commits recientes
git branch                    # confirmar rama activa
docker compose ps             # estado actual del stack
```

Si hay cambios sin commitear de una sesión anterior: analizarlos y commitearlos antes de empezar.

### 2. Si el cambio incluye frontend (website/)

Verificar el build antes de commitear — obligatorio:

```bash
cd /root/website && npm run build
```

El build debe completar sin errores TypeScript ni de compilación. Si falla, corregir antes de continuar.

### 3. Verificar .gitignore antes de `git add` en directorios nuevos

```bash
ls -la <directorio>/
```

Artefactos que nunca deben ir al repositorio:
- `*.db` — bases de datos runtime
- `node_modules/ .next/ dist/` — dependencias y builds
- `.env .env.*` — secretos
- `*.zip` — backups

### 4. Commitear

```bash
git add <archivos-específicos>
git commit -m "tipo: descripción clara del cambio"
```

Commitear por tarea lógica, no acumular cambios de múltiples tareas.

### 5. Leer el workflow de deploy antes de push a main

```bash
# Leer antes de modificar o si hay dudas:
cat /root/.github/workflows/deploy.yml
```

### 6. Push a GitHub

```bash
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
```

Ver [[https_git_push]] para el patrón completo.

### 7. Monitorear GitHub Actions

Verificar en `https://github.com/erikjosehrnndz-crypto/hermes-stack/actions` que el workflow de deploy complete sin errores.

El pipeline automático ejecuta:
- `git pull /root` en el VPS
- `docker compose up -d --build`
- Health checks de [[litellm_router]] y [[hermes_agent]]
- Rollback a `HEAD~1` si los health checks fallan

### 8. Verificar health checks manualmente

```bash
source /root/.env
curl -f -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
curl -f http://127.0.0.1:8080/health
```

Solo declarar el deploy exitoso después de verificación manual exitosa.

## Notas

- **No hacer force push a main** — el CI/CD usa `git pull`, un rebase rompe la historia en el VPS.
- **SSH no funciona para push** — siempre usar el patrón HTTPS con token.
- **LiteLLM health check requiere auth** — sin el header `Authorization`, el curl retorna 401 y parece fallar cuando en realidad el servicio está bien.
- **Si el build de website/ falla en CI** — probablemente falta `public/.gitkeep` o hay un error TypeScript que solo aparece en build frío.

## Gotchas

- Usar `next.config.mjs` no `next.config.ts` en Next.js 14.2.x — ver [[nextjs_app_router]].
- Nombres de servicio en compose vs nombres de contenedor son diferentes — ver [[docker_compose_stack]].
- El rollback automático revierte solo el último commit; si hay múltiples commits problemáticos, hacer rollback manual.

## Véase también

- [[ci_cd_pipeline]] — arquitectura completa del pipeline
- [[https_git_push]] — patrón de push con token
- [[frontend_changes]] — si el deploy incluye cambios en website/
- [[adding_new_service]] — si el deploy introduce un nuevo servicio Docker
