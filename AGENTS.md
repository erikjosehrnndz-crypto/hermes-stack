# AGENTS.md — Arquitectura Hermes Stack v2.0 + Integración Modular

> **Este archivo define las reglas de convivencia y el comportamiento del sistema integrado.**
> **Ubicación:** `/root/AGENTS.md` (raíz del proyecto)
> **Generado:** 2026-05-26 — Post-integración Hermes Workspace + advanced-skills + OverCR

---

## 1. Visión General de la Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HUMANO (Tú)                                │
│                   Chat en Workspace UI (3002)                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              HERMES WORKSPACE (3002) — Frontend Único            │
│  • Chat SSE • Terminal PTY • Memory Browser • Skills Manager     │
│  • Swarm Mode: builder │ reviewer │ qa (definidos, pendiente backend)│
│  • Conductor Mode (falta conexión a Hermes Gateway 8642)          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
┌──────────────────────────┐      ┌──────────────────────────────────┐
│  HERMES AGENT v2.0      │      │  HERMES AGENT (Docker)          │
│  (Yo — CLI/Local)       │      │  (aiohttp :8080)               │
│  • delegate_task         │      │  • Pipeline de voz /api/voice  │
│  • skills/agents-dir    │      │  • Conectado a LiteLLM :4000    │
│  • smart-replan.yaml    │      │  • Redis cache :6379            │
└───────────┬──────────────┘      └───────────┬────────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OVERCR (Gobernanza L1-L6)                     │
│  • Approval Gates • Packet Validation • Audit Trail               │
│  • Sandbox v2.6 (14-command allowlist)                         │
│  • Intercepta: git push, docker compose, curl externo, emails  │
│  • Estado: Instalado, tests 30/31 PASS, demo verificado         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INFRAESTRUCTURA DOCKER                         │
│  • hermes (:8080) • website (:3001) • litellm (:4000)          │
│  • prometheus (:9090) • grafana (:3000) • redis (:6379)        │
│  • whisper-stt (:9000) • filebrowser (:8095) • autoheal        │
│  • Redes: backend │ monitoring                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Módulos y Responsabilidades

### 2.1 Hermes Agent v2.0 (Núcleo de Orquestación)
- **Rol:** Agent principal que ejecuta tareas, coordina sub-agentes, gestiona memoria.
- **Skills cargados:**
  - `agents-dir-rules` → Inyección automática de `AGENTS.md` por directorio en `delegate_task`.
  - `smart-replan` → Failure Auto-Replan (1 reintento con análisis de `exit_reason`).
- **Reglas de ejecución:**
  - Antes de `delegate_task`, leer `AGENTS.md` del directorio destino.
  - Si `delegate_task` falla, analizar `exit_reason` y reintentar 1 vez con estrategia ajustada.
  - No ejecutar acciones mutativas sin confirmación si OverCR está activo.

### 2.2 Hermes Workspace (Frontend Unificado)
- **Rol:** Interfaz web única para chat, archivos, memoria, terminal y Swarm.
- **Estado:** Corriendo en `http://127.0.0.1:3002` (modo demo, sin backend conectado).
- **Swarm Mode:** Roles `builder`, `reviewer`, `qa` definidos en su `AGENTS.md` interno.
- **Limitación actual:** Espera Hermes Gateway en puerto `8642` (nuestro stack usa `8080` para voz).
- **Acción futura:** Adaptar Workspace para conectar a `/process` en `8080` o instalar Hermes upstream.

### 2.3 OverCR (Capa de Gobernanza)
- **Rol:** Guardián de acciones externas y mutaciones del sistema.
- **Validación L1-L6:**
  - **L1-L3 (Lecturas):** Pasan sin aprobación.
  - **L4-L6 (Escrituras/Externas):** Requieren aprobación explícita.
- **Acciones que intercepta:**
  - `git push` (repositorios remotos)
  - `docker compose up/down/restart`
  - `curl -X POST` a hosts no locales
  - `send_message` (Telegram, Discord, email)
  - Cualquier comando que modifique archivos fuera de `/tmp/`
- **Estado:** Instalado en `/root/integrations/overcr/`, runtime verificado, tests 30/31 PASS.
- **Integración futura:** Necesita webhook a Workspace para diálogos de aprobación visual.

### 2.4 LiteLLM Router + Modelos
- **Rol:** Proxy unificado para modelos LLM (Gemini, GPT, Claude vía OpenRouter).
- **Endpoint:** `http://litellm:4000` (red `backend` de Docker).
- **Modelo activo:** `openrouter/google/gemini-2.5-flash`.
- **Métricas:** Prometheus scrapea `/metrics/` en puerto `9090`.

---

## 3. Reglas de Convivencia de Módulos

### 3.1 Jerarquía de Autoridad
1. **Humano** → Aprobación final de acciones L4-L6.
2. **OverCR** → Rechaza o aprueba acciones mutativas basado en L1-L6.
3. **Hermes Agent (yo)** → Ejecuta tareas, respeta reglas de OverCR.
4. **Workspace** → Presenta información, no tiene autoridad de ejecución.

### 3.2 Flujo de Tarea con Validación
```
Humano → Workspace (input) → Hermes Agent (procesa)
         ↓
         → Lee AGENTS.md local (agents-dir-rules)
         ↓
         → delegate_task con context inyectado
         ↓
         → Si acción mutativa: consulta OverCR
         ↓
         → OverCR evalúa L1-L6 → Aprobación Humano (si L4+)
         ↓
         → Ejecución → Auto-replan si falla (smart-replan)
```

### 3.3 Reglas de Archivos y Directorios
- **`/root/AGENTS.md`** (este archivo): Reglas globales del proyecto.
- **`/root/<subdir>/AGENTS.md`**: Reglas específicas por directorio de trabajo.
- **`/root/.hermes/skills/`**: Skills cargados por Hermes Agent (yo).
- **`/root/hermes/skills/`**: Skills dentro del contenedor Docker `hermes-agent`.
- **`/root/integrations/`**: Repos clonados de integración (no commitear a main).

### 3.4 Reglas de Commits y Git
- **Nunca commitear:** `.env`, `*.db`, `node_modules/`, `.next/`, `*.log`, `backups/`.
- **`git add` siempre desde `/root`** — nunca desde subdirectorio.
- **Push HTTPS:** Incrustar token en remote URL, restaurar URL limpia después.
- **Push require aprobación OverCR L4+** (cuando esté integrado completamente).
- **Una tarea activa por sesión** — registrar otras en `PENDIENTES.md`.

### 3.5 Reglas de Auto-Reparación (Failure Auto-Replan)
- Si `delegate_task` falla:
  1. Leer `exit_reason` del sub-agente.
  2. Clasificar: `timeout`, `file_not_found`, `permission_denied`, `command_fail`.
  3. Ajustar: cambiar `workdir`, añadir `context`, simplificar comando.
  4. **Reintentar 1 sola vez** (evitar bucle infinito).
  5. Si falla de nuevo: reportar cadena `[Original] → [Retry] → [Final]`.
- **Log de reparaciones:** `/root/integrations/auto_repair.log`

### 3.6 Reglas de Swarm Mode (Futuro)
- **Roles disponibles:** `builder` (código), `reviewer` (código/revisión), `qa` (pruebas).
- **Builder:** Implementa, usa TDD (`test-driven-development` skill).
- **Reviewer:** Gated reviews, usa `requesting-code-review` skill.
- **QA:** Verifica comportamiento, usa `dogfood` skill.
- **Orquestador:** Yo (Hermes Agent) ruteo tareas basado en complejidad.

---

## 4. Estado de la Integración (2026-05-27)

### Mapa de puertos completo

| Servicio | Puerto host | Subdominio | Estado |
|---|---|---|---|
| hermes-agent (docker) | `127.0.0.1:8080` | `hermes.el80.space` | ✅ Healthy |
| hermes-gateway (CLI) | `127.0.0.1:8642` | — (interno) | ✅ Running |
| hermes-dashboard (CLI) | `127.0.0.1:9119` | `dashboard.el80.space` | ✅ Running |
| hermes-workspace (docker) | `127.0.0.1:3002` | `workspace.el80.space` | ✅ Healthy |
| litellm-router | `127.0.0.1:4000` | `litellm.el80.space` | ✅ Healthy |
| 9router | `127.0.0.1:20128` | `router.el80.space` | ✅ Healthy |
| grafana | `127.0.0.1:3000` | `grafana.el80.space` | ✅ Up |
| hermes-website | `127.0.0.1:3001` | `docs.el80.space` | ✅ Healthy |
| filebrowser | `127.0.0.1:8095` | — | ✅ Healthy |
| prometheus | `127.0.0.1:9090` | — | ✅ Up |
| whisper-stt | `127.0.0.1:9000` | — | ✅ Healthy |

### Componentes integrados

| Componente | Estado | Notas |
|---|---|---|
| Hermes Workspace | ✅ **Conectado** | `HERMES_API_URL=http://127.0.0.1:8642`, `network_mode: host` |
| Hermes Gateway CLI | ✅ **Activo** | `hermes_cli.main gateway run --replace` en `:8642` |
| Hermes Dashboard CLI | ✅ **Activo** | `hermes dashboard` en `:9119`, sessions/skills/memory/jobs |
| advanced-skills | ✅ Integrado | `/root/.hermes/skills/agents-dir-rules/` |
| smart-replan | ✅ Disponible | `/root/.hermes/personalities/` |
| OverCR Gate (plugin) | ✅ **Activo** | `~/.hermes/plugins/overcr-gate/plugin.py`, intercepta L4-L6 |
| 9router | ✅ **Restaurado** | 16 provider connections (Claude, Codex, GitHub, Gemini, etc.) |
| Stack Docker | ✅ 13 servicios Up | `/root/docker-compose.yml` |

### Workspace → Gateway connection
```
Workspace (:3002) → HTTP → hermes-gateway (:8642) → /v1/chat/completions
                         → /api/sessions, /v1/models, /health
                         → /v1/runs/{id}/approval (OverCR gate)
Workspace (:3002) → HTTP → hermes-dashboard (:9119) → sessions/skills/memory
```

### OverCR Gate (plugin.py)
- Intercepta `pre_tool_call` en Hermes Agent CLI
- L4: `git push`, `docker compose up -d`, `kubectl apply`, `crontab -e`
- L5: `curl -X POST <external>`, `wget --post-data <external>`, `mail/sendmail`
- L6: escritura en `AGENTS.md`, `CLAUDE.md`, `soul.md`
- Bloqueo → mensaje con instrucción de aprobar vía `workspace.el80.space` → ícono campana

### Pendiente de completar
1. **Hermes dashboard persistencia** — actualmente `nohup` manual; añadir a systemd o supervisord.
2. **OverCR approval webhook** — integrar `/v1/runs/{id}/approval` con el botón de aprobación de Workspace.
3. **Tokens OAuth** — los 9 tokens OAuth del backup expiraron (2026-05-23); reautenticar via `router.el80.space`.

---

## 5. Comandos de Verificación

```bash
# Estado completo del stack
cd /root && docker compose ps

# Workspace
curl -sf http://127.0.0.1:3002/ | head -1         # → <!DOCTYPE html>
curl -sf http://127.0.0.1:8642/health              # → {"status":"ok","platform":"hermes-agent"}
curl -sf http://127.0.0.1:9119/health | head -3    # → HTML del dashboard

# 9router
curl -sf http://127.0.0.1:20128/api/health         # → {"ok":true}

# OverCR gate
python3 -c "
import sys; sys.path.insert(0,'/root/.hermes/plugins/overcr-gate')
from plugin import _classify_command
print(_classify_command('git push origin main'))   # → ('L4', 'git push ...')
print(_classify_command('ls /tmp'))                # → (None, None)
"

# Hermes health checks
source /root/.env
curl -sf -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
curl -sf http://127.0.0.1:8080/health

# Ver log de auto-reparación
cat /root/integrations/auto_repair.log 2>/dev/null || echo "no log yet"
```

---

## 6. Notas de Seguridad

- **OverCR L6:** Bloquea cualquier intento de modificar `AGENTS.md` o reglas de gobernanza sin aprobación triple.
- **Workspace:** Modo demo actual no tiene auth (`HERMES_ALLOW_INSECURE_REMOTE=1`). Activar `HERMES_PASSWORD` antes de exposición externa.
- **Docker:** Redes `backend` y `monitoring` aisladas. Solo `filebrowser` y `grafana` exponen puertos a localhost.

---

*Documento generado automáticamente por Hermes Architect Agent.*
*Integración ejecutada: 2026-05-26. Spike report: `/root/.hermes/plans/spike-report.md`.*
*Log de auto-reparación: `/root/integrations/auto_repair.log`.*
