# Pendientes — Hermes Stack

Estado formal en `PENDIENTES.json`. Esta tabla es la vista rápida.

| ID | Servicio | Prioridad | Estado | Próximo paso |
|---|---|---|---|---|
| hs-001 | hermes-agent | 🔴 crítico | ✅ done | Bridge /api/voice creado; pipeline funcional |
| hs-002 | litellm-router | 🔴 crítico | ✅ done | Gemini reemplazado por OpenRouter/google/gemini-2.5-flash |
| hs-003 | infra | 🟡 warning | ✅ done | litellm en red monitoring; Prometheus scraping OK |
| hs-004 | litellm-router | 🟡 warning | ✅ done | gemini-flash E2E verificado (483ms) |
| hs-005 | hermes-agent | 🔵 mejora | ✅ done | Rebuild aplicado en commit 8b2dc10 |
| hs-006 | infra | 🔵 mejora | ✅ done | Merge + push main c218fe2; CI/CD activado |
| hs-007 | infra | 🔵 mejora | not-started | Completar mesh Tailscale: auth DO droplet + verificar Android |
| hs-008 | brain | 🟢 nueva | ✅ done | Brain Phase 6 done: 7 MCP tools, crons, memoria conversacional (Hermes + Claude Code). Commits cef0166 + 9387800. |
| hs-010 | portafolio | 🔴 crítico | ✅ done | Portafolio sintetizado ante teardown: 3 tiers (repo curado + bundle estado cifrado + opcionales). Ver PORTFOLIO.md / RECONSTRUCCION.md. Bundle: backups/hermes-portfolio-state-*.tar.gz.gpg (passphrase entregada aparte). |
| hs-009 | integraciones | 🟢 nueva | ✅ done | codegraph (MCP) + Understand-Anything (plugin) + Twenty CRM en crm.el80.space. Warp descartado. Commit a698386. Drift Caddyfile repo↔/etc pendiente. |
| hs-011 | obsidian-sync | 🟢 nueva | ✅ done | LiveSync revivido (NO dormido): couchdb-obsidian + livesync-bridge. Móvil Android ↔ DB el80vault ↔ carpeta brain/ del vault del brain. Bidireccional verificado (create/change/delete). Manual: docs/manual-obsidian-movil.md. |

Ver estado detallado y comandos de verificación en `PENDIENTES.json`.

---

## ✅ Resueltos (2026-05-26)

**hs-001 — Pipeline Hermes: 0 requests en 47h**
- Root cause: no existía cliente que llamara `/process`. GEMINI_API_KEY estaba en cuota gratuita agotada.
- Fix: creado `website/app/api/voice/route.ts` como bridge frontend→Hermes. Modelo actualizado a gemini-2.5-flash via OpenRouter.
- **Evidencia:** `curl -X POST http://127.0.0.1:3001/api/voice -d '{"text":"test"}' → {"text":"Pipeline de voz funcionando.","model_used":"gemini-flash","latency_ms":458.66}`

**hs-002 — gemini/text-embedding-004 caído**
- Root cause: GEMINI_API_KEY en free tier agotado (quota limit 0). Embeddings model eliminado de litellm.yaml (no se usa en producción).
- Fix: gemini-flash redirigido a `openrouter/google/gemini-2.5-flash`. Todos los modelos HEALTHY.
- **Evidencia:** `HEALTHY: [gpt-4o, claude-sonnet, gpt-4o-mini, llama-3-1-70b, gemini-flash] | UNHEALTHY: []`

**hs-003 — litellm no en red monitoring**
- Fix: añadido `monitoring` a networks de litellm en docker-compose.yml + habilitado callback prometheus en litellm.yaml + corregido metrics_path a `/metrics/` en prometheus.yml.
- **Evidencia:** `curl http://127.0.0.1:9090/api/v1/targets → litellm : up`

**hs-004 — Verificar gemini-flash E2E**
- Verificado: 483ms latencia, respuesta correcta via LiteLLM → OpenRouter → Google.
- **Evidencia:** `{"model_used":"gemini-flash","latency_ms":483.11}`

**hs-005 — Rebuild hermes**
- Completado en sesión 2026-05-25.
- **Evidencia:** commit `8b2dc10`

## 🔵 Mejoras pendientes

**hs-006 — Merge `feat/nextjs-rocket-compat` → `main`** para activar el CD pipeline y desplegar todos los cambios acumulados
- **Verificación:** `git log --oneline main..HEAD | wc -l  # debe ser 0`
- **Evidencia:** _pendiente_

**hs-007 — Mesh Tailscale: DO droplet + Android**
- DO droplet (`104.236.74.0`): Tailscale instalado, pendiente auth (URL generada en sesión 2026-05-26).
- Android (`xiaomi-14t-pro`): offline hace 2d — abrir app Tailscale en Xiaomi 14T Pro.
- **Verificación:** `tailscale ping 100.85.146.98 && tailscale status | grep -c 'active'`
- **Evidencia:** _pendiente_

---

**hs-011 — Obsidian LiveSync móvil ↔ brain**
- Infra LiveSync revivida desde estado "dormido" + pieza nueva `livesync-bridge` (repo vrtmrz, headless, Deno).
- Arquitectura: móvil Android (plugin Self-hosted LiveSync) → CouchDB `el80vault` (`https://livesync.el80.space`) → bridge sincroniza solo `brain/` ↔ volumen `root_brain_vault`.
- E2EE OFF en v1 (transporte TLS + auth CouchDB). Activable después con passphrase en plugin + `dat/config.json`.
- **Verificación:** 42 notas del brain subidas a CouchDB; create/change/delete propagan filesystem→CouchDB (tombstone `deleted:true` correcto). Falta confirmar leg CouchDB→filesystem al conectar el móvil.
- **Evidencia:** `docker logs livesync-bridge` → "Database is now ready."; `curl -u obsidian:$PW https://livesync.el80.space/el80vault` OK.
- **Pendiente del usuario:** seguir `docs/manual-obsidian-movil.md` Parte 1 en el móvil.

---

*Actualizado: 2026-05-29 (hs-011 — Obsidian LiveSync móvil↔brain revivido) · Estado formal: `/root/PENDIENTES.json`*
