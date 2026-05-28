# AGENTS.md — Hermes Stack (entry compacto)

Reglas operativas del sistema integrado. Detalle completo en `CLAUDE.md`. Este archivo es el **entry rápido** para agentes nuevos o contexto recién comprimido.

---

## 1. Módulos

| Componente | Puerto | Rol |
|---|---|---|
| Hermes Agent (Docker) | `:8080` | Pipeline de voz `/api/voice`, conectado a LiteLLM, Redis cache |
| Hermes Gateway (CLI) | `:8642` | `/v1/chat/completions`, `/api/sessions`, OverCR approval `/v1/runs/{id}/approval` |
| Hermes Dashboard (CLI) | `:9119` | sessions / skills / memory / jobs |
| Hermes Workspace | `:3002` | Frontend unificado: chat SSE, terminal PTY, memory browser, swarm |
| Hermes Website | `:3001` | Next.js docs + bridge `/api/voice` |
| LiteLLM Router | `:4000` | Proxy LLM → OpenRouter (gemini-2.5-flash default) |
| 9router | `:20128` | 16 provider connections (Claude, Codex, GitHub, Gemini…) |
| Whisper STT | `:9000` | Transcripción |
| Grafana / Prometheus / Redis | `:3000` / `:9090` / `:6379` | Observabilidad + cache |
| Filebrowser | `:8095` | Acceso archivos |

Redes: `backend` (servicios) · `monitoring` (métricas).

## 2. Skills + personalidades activos

- `/root/.hermes/skills/agents-dir-rules/` — inyecta `AGENTS.md` del directorio destino antes de `delegate_task`
- `/root/.hermes/personalities/smart-replan.yaml` — failure auto-replan, 1 reintento con `exit_reason` ajustado
- `~/.hermes/plugins/overcr-gate/plugin.py` — intercepta `pre_tool_call` L4-L6

## 3. Hard constraints

**Autoridad:** Humano > OverCR > Hermes Agent > Workspace. Workspace nunca ejecuta sin pasar por Agent.

**OverCR L4-L6 (requieren aprobación):**
- L4: `git push`, `docker compose up -d`, `kubectl apply`, `crontab -e`
- L5: `curl -X POST` externo, `mail/sendmail`, webhooks
- L6: escritura en `AGENTS.md`, `CLAUDE.md`, `soul.md`

**Git (resumen — detalle en CLAUDE.md):**
- Nunca commitear `.env`, `*.db`, `node_modules/`, `.next/`, `*.log`, `backups/`
- `git add` siempre desde `/root` (no desde subdirectorio)
- Push HTTPS con token incrustado, restaurar URL limpia después
- `git push` requiere aprobación OverCR L4

**Scope:**
- ≤ 1 tarea activa por sesión — registrar el resto en `PENDIENTES.md`
- Auto-replan: máximo 1 reintento, luego reportar cadena `[Original]→[Retry]→[Final]`

**Archivos:**
- `/root/AGENTS.md` — reglas globales (este archivo)
- `/root/<subdir>/AGENTS.md` — reglas locales por directorio
- `/root/.hermes/skills/` — skills del Agent CLI · `/root/hermes/skills/` — skills dentro del contenedor Docker
- `/root/integrations/` — repos clonados, no commitear a main

## 4. Definition of Done (toda tarea)

1. Implementación existe en código
2. Verificación ejecutada (no "debería funcionar")
3. Evidencia: commit hash o output en `PENDIENTES.json/.md` o `SESSION_HANDOFF.md`
4. `docker compose ps` muestra todos los servicios Up

## 5. Comandos críticos

```bash
# Pipeline único
make doctor                                              # 6 pasos: repo → docker → health → lint → harness → pendientes
make check                                               # build + health + lint

# Stack
docker compose ps
curl -sf http://127.0.0.1:8080/health                    # hermes
curl -sf http://127.0.0.1:8642/health                    # gateway CLI
curl -sf http://127.0.0.1:20128/api/health               # 9router
source /root/.env && curl -sf -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health

# OverCR classifier (sanity)
python3 -c "import sys; sys.path.insert(0,'/root/.hermes/plugins/overcr-gate'); from plugin import _classify_command; print(_classify_command('git push origin main'))"
```

## 6. Pendientes activos / handoff

Estado autoritativo en `/root/PENDIENTES.json`. Resumen visible en `/root/PENDIENTES.md`. Trabajo en curso entre sesiones en `/root/SESSION_HANDOFF.md`.

Pendientes operativos conocidos:
1. Hermes dashboard `:9119` — actualmente `nohup`, falta systemd/supervisord
2. OverCR approval webhook → botón aprobación en Workspace
3. 9 tokens OAuth expiraron 2026-05-23 — reautenticar via `router.el80.space`

## 7. Notas de seguridad

- OverCR L6 bloquea modificación de `AGENTS.md` / `CLAUDE.md` / `soul.md` sin aprobación triple.
- Workspace en modo demo no tiene auth (`HERMES_ALLOW_INSECURE_REMOTE=1`) — activar `HERMES_PASSWORD` antes de exposición externa.
- Redes Docker `backend` y `monitoring` aisladas; solo `filebrowser` y `grafana` exponen puertos en localhost.

---

*Para detalle de cualquier sección → `CLAUDE.md`. Spike report integración: `/root/.hermes/plans/spike-report.md`.*
