El siguiente paso es: hacer merge de `feat/nextjs-rocket-compat` → `main` (hs-006) para activar el CD pipeline y desplegar los 26 commits acumulados.

**Trabajo completado en sesión 2026-05-26:**
- hs-001: creado `website/app/api/voice/route.ts` (bridge frontend→Hermes). Pipeline E2E verificado: 458ms
- hs-002: GEMINI_API_KEY en cuota free agotada; gemini-flash migrado a `openrouter/google/gemini-2.5-flash`
- hs-003: litellm en red monitoring + callbacks prometheus + metrics_path `/metrics/`; `litellm : up` en Prometheus
- hs-004: gemini-flash E2E verificado (483ms, model healthy)
- hs-005: rebuild hermes ya estaba en commit 8b2dc10
- Corregido healthcheck website (IPv6→IPv4, path `/health`→`/api/health`)

**Commits clave:** `4f2540d` (stack fixes), `/evolve` actual

**Credenciales control-center (de sesión anterior):**
- SSH Droplet: `ssh -i /root/.ssh/do_droplet_key root@104.236.74.0`
- Grafana: admin / HermesControl2026!
- Compose en Droplet: `/root/control-center/`
