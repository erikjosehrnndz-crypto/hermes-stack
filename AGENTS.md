# AGENTS.md — Hermes Stack

## Proyecto
Plataforma AI autohospedada en el80.space. Stack: Python 3.12 + Next.js 14 + Docker + Prometheus.

Componentes principales:
- `hermes/` — agente conversacional aiohttp (Python), puerto 8080
- `website/` — UI Next.js App Router, puerto 3001
- `config/` — LiteLLM router + Prometheus + alertas
- `docker-compose.yml` — 11 servicios en redes `backend` y `monitoring`

## Startup sequence

```bash
git status && git log --oneline -5 && git branch
docker compose ps
rm -f /tmp/claude_progress                         # limpiar barra de progreso stale
cat /root/SESSION_HANDOFF.md 2>/dev/null           # handoff de sesión anterior
cat /root/PENDIENTES.md                            # tareas activas y bloqueadores
```

Si hay cambios sin commitear de sesión anterior: analizar → commitear o descartar **antes** de trabajo nuevo.

## Hard constraints

1. Nunca commitear `.env`, `*.db`, `node_modules/`, `.next/`, `*.log`, `backups/`
2. `npm run build` antes de cualquier commit de frontend
3. `git add` **siempre desde** `/root` — nunca desde subdirectorio
4. Push HTTPS: incrustar token en remote URL, restaurar URL limpia después
5. Leer archivo **completo** antes de editar — nunca appendear sin ver el final
6. **Una tarea activa por sesión** — registrar otras en PENDIENTES.md, no empezarlas
7. Sub-agentes escriben a `/tmp/<task_id>.md` antes de terminar
8. Opus 4.7 → orquestador; Haiku → extracción de datos; Sonnet → síntesis
9. Nunca saltarse git hooks (`--no-verify`)
10. Health check obligatorio antes de declarar un deploy exitoso

## Verification gate

```bash
make check          # build + health + lint — un solo comando
make health-check   # solo health checks de servicios
make build-check    # solo build Next.js
make status         # docker compose ps
```

## Definition of Done

Una tarea está **done** cuando se cumplen los 4 criterios:
1. Implementación existe en código
2. Verificación ejecutada (no "debería funcionar" — correr el comando real)
3. Evidencia registrada (commit hash o output del comando en PENDIENTES.md/SESSION_HANDOFF.md)
4. Stack en estado reiniciable: `docker compose ps` muestra todos los servicios Up

## Tarea activa

Ver `/root/PENDIENTES.md` para estado actual. Actualizar antes de cerrar sesión.

## Documentación de referencia

| Tema | Fuente |
|---|---|
| Git, permisos, Next.js, LaTeX, Docker, orquestación | `CLAUDE.md` (carga automática) |
| Arquitectura completa del stack | `Hermes_Stack_Blueprint.pdf` (52 pp) |
| Diagrama de servicios | `docker-compose.yml` |
| Tareas activas | `PENDIENTES.md` + `PENDIENTES.json` |
| Estado de sesión en curso | `SESSION_HANDOFF.md` (si existe) |
