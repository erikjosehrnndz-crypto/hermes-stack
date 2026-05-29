# PORTFOLIO — Hermes Stack (portafolio sintetizado)

> Manifiesto único del sistema. Compilado el **2026-05-29** ante la destrucción de la instancia VPS.
> Curado, sin redundancias, con todo lo necesario para reconstruir el stack en su versión ideal.
> Para **levantarlo paso a paso**, ver `RECONSTRUCCION.md`.

---

## Qué es el Hermes Stack

Plataforma IA conversacional autohospedada (dominio **el80.space**): pipeline de voz E2E < 500 ms
(Whisper STT local → LiteLLM → OpenRouter/Gemini → ElevenLabs TTS), con segundo cerebro RAG
(**brain**), router multi-proveedor (**9router**), web pública, y stack de observabilidad
(Prometheus/Grafana/cAdvisor) — todo tras **Caddy** (TLS automático) con hardening de contenedores
y auto-curación (autoheal + watchdog systemd).

---

## El portafolio en 3 tiers

### TIER 1 — Repo canónico (este repositorio git → GitHub)
Fuente de verdad. Sobrevive a la destrucción. Contiene **solo** lo curado:

| Área | Contenido |
|---|---|
| Código | `hermes/` (agente), `brain/` (RAG), `website/` (Next.js), `9router/Dockerfile` |
| Orquestación | `docker-compose.yml` (núcleo, 14 servicios), `docker-compose.optional.yml` (Tier 3), `Makefile`, `.env.template` |
| Infra | `infra/` (Caddyfile, bootstrap-server.sh, setup-caddy.sh, units systemd, tailscale-grants), `scripts/`, `.github/workflows/deploy.yml` |
| Config | `config/litellm.yaml`, `config/prometheus.yml`, `config/alerts.yml`, `config/couchdb/local.ini.template` |
| Conocimiento | `docs/` (rules×12, blueprint, roadmap, manuales .tex/.pdf), `wiki/` (35 notas), README/CLAUDE/AGENTS/PENDIENTES |
| Integraciones | `integrations/kamatera/` (MCP), `twenty/docker-compose.yml` (CRM opcional) |

### TIER 2 — Bundle de estado (cifrado, FUERA de git)
`backups/hermes-portfolio-state-AAAAMMDD-HHMM.tar.gz.gpg` — **no commitear nunca**.
Cifrado GPG simétrico; la passphrase se entregó por separado (NO está en este repo).
Contiene lo que git no puede/debe llevar:

- **Secretos:** `.env`, credenciales Oracle `Wallet_NEXUSMEMORY`, auth OAuth de 9router.
- **Conocimiento (volúmenes):** `brain_vault`, `brain_lance`, `brain_graph`, `ruvector.db` canónico.
- **Estado del agente:** `.hermes/` (memorias, SOUL.md, state.db, kanban, plans).
- **Harness Claude:** `.claude/projects/-root/memory/` (13 memorias), commands, templates, settings.json.
- **Local sin remote:** `hermes-deploy.tar.gz`, `filebrowser.db`.
- **NO incluye** (telemetría/regenerable): `brain_models` (1.8 GB, se re-descarga de HuggingFace al primer arranque), `prometheus_data`, `grafana_data`.

### TIER 3 — Opcionales revivibles (preservados, NO en el arranque por defecto)
Excluidos del stack ideal por eficiencia; nada se pierde:

| Servicio | Cómo revivir |
|---|---|
| **hermes-workspace** (panel) | `docker compose -f docker-compose.yml -f docker-compose.optional.yml up -d` |
| **Obsidian LiveSync** (couchdb-obsidian) | idem ↑ + restaurar vol `couchdb_data` si se respaldó (estaba dormido) |
| **Twenty CRM** | `cd twenty && docker compose up -d` (stack propio, crm.el80.space) |
| **9remote** (control remoto) | daemon host en `.9remote/` (estaba en el bundle si se incluyó; fuera de compose) |

### Integraciones externas (repos propios — se clonan, no van en este repo)
| Ruta | Origin |
|---|---|
| `integrations/overcr` | https://github.com/GuideboardLabs/overcr.git |
| `integrations/hermes-agent-advanced-skills` | https://github.com/remix2111/hermes-agent-advanced-skills.git |
| `integrations/hermes-workspace` | https://github.com/outsourc-e/hermes-workspace.git |

---

## Mapa de servicios, puertos y subdominios

| Servicio | Puerto (127.0.0.1) | Subdominio | Tier |
|---|---|---|---|
| hermes-agent | 8080 | hermes.el80.space | núcleo |
| litellm-router | 4000 | litellm.el80.space | núcleo |
| 9router | 20128 | router.el80.space | núcleo |
| brain / brain-worker | 8765 | — interno | núcleo |
| whisper-stt | 9000 | — interno | núcleo |
| redis | — | — interno | núcleo |
| website (Next.js) | 3001 | docs.el80.space | núcleo |
| grafana | 3000 | grafana.el80.space | núcleo |
| prometheus | 9090 | metrics.el80.space (basic_auth) | núcleo |
| cadvisor / node-exporter / autoheal | — | — interno | núcleo |
| filebrowser | 8095 | files.el80.space | núcleo |
| hermes-workspace | 3002 (host) | — | opcional |
| couchdb-obsidian | 5984 | livesync.el80.space | opcional |
| twenty-crm | 3005 | crm.el80.space | opcional |

Secretos requeridos en `.env` (ver `.env.template`): `LITELLM_MASTER_KEY`, `OPENROUTER_API_KEY`,
`GEMINI_API_KEY`, `ELEVENLABS_API_KEY`/`VOICE_ID`, `BRAIN_API_TOKEN`, `ROUTER_JWT_SECRET`/`INITIAL_PASSWORD`,
`COUCHDB_PASSWORD`, `FILEBROWSER_PASSWORD`, `DIGITALOCEAN_TOKEN`, `RUNPOD_API_KEY`.

---

## Qué se descartó (filtrado de redundancias)

Caches (`.cache` 2.9 G, `.npm` 2.8 G, `.nvm` 439 M), `node_modules`/`.next`/`__pycache__`,
backups viejos y telemetría, `hermes_bp/` (LaTeX duplicado de `docs/`), DBs duplicadas
(`website/ruvector.db`, `docs/ruvector.db`), `.codegraph`/`.understand-anything` (regeneran),
archivos personales (manuales de frenos), `Sync/`, `snap/`. **De ~10 GB → repo de pocos MB +
bundle de estado de ~14 MB** (modelos excluidos, se re-descargan).

---

## Decisiones de diseño preservadas (no obvias)

1. **Latencia:** Whisper local (sin coste/envío de audio), ElevenLabs Flash v2.5 por WebSocket persistente, routing por latencia en LiteLLM, caché semántico Redis.
2. **Seguridad multicapa:** Caddy único punto público, puertos solo en `127.0.0.1`, `no-new-privileges` + `cap_drop: ALL`, iptables DOCKER-USER, contenedores non-root.
3. **Auto-curación:** healthchecks → autoheal (30 s) → docker-watchdog systemd (60 s); CI/CD con rollback automático a `HEAD~1` si el health check post-deploy falla.
4. **Arquitectura de instrucciones:** `CLAUDE.md` router lean + `docs/rules/*.md` por dominio (carga bajo demanda) — capacidad ilimitada sin bloat.
5. **Healthchecks con `127.0.0.1`** (no `localhost`) para evitar resolución IPv6 en Alpine.
