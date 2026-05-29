# SESSION_HANDOFF — 2026-05-29 → próxima sesión

## Estado: portafolio sintetizado COMPLETO. La instancia puede destruirse.

Rama: `main`. Tarea hs-010 (portafolio para teardown) cerrada.

## Hecho esta sesión (hs-010)
Portafolio sintetizado en 3 tiers ante la destrucción de la instancia:

1. **Tier 1 — repo curado** (este git, pusheado a GitHub):
   - Desindexado cruft: `hermes_bp/` (LaTeX duplicado de `docs/`).
   - `.gitignore` ampliado: `*.db`, `*.zip`, `*.tar.gz.gpg`, artefactos LaTeX, `Sync/`, `snap/`, `backups/`, Wallet, personales, integraciones externas (repos propios).
   - Añadido a git: `wiki/` (35 notas), `docs/` (md/txt/tex/pdf), `hermes/personalities` + `hermes/skills`, `integrations/kamatera`.
   - `docker-compose.yml` recortado a **14 servicios núcleo** (+ filebrowser); opcionales movidos a **`docker-compose.optional.yml`**.
   - Nuevos: **`PORTFOLIO.md`** (manifiesto) y **`RECONSTRUCCION.md`** (runbook manual).

2. **Tier 2 — bundle de estado CIFRADO** (NO en git):
   - `backups/hermes-portfolio-state-20260529-0357.tar.gz.gpg` (~14 MB).
   - Contiene: `.env`, Wallet Oracle, auth 9router, volúmenes brain (vault/lance/graph), `.hermes/` (memorias/SOUL/state.db), memoria Claude, `ruvector.db`, `filebrowser.db`, `hermes-deploy` local.
   - Excluye modelos (1.8 GB, se re-descargan) y telemetría.
   - **Passphrase GPG entregada al usuario en el chat** (también en `/root/.portfolio-passphrase`, que muere con la instancia). Verificado que descifra OK.

3. **Tier 3 — opcionales revivibles:** hermes-workspace, couchdb-obsidian, Twenty CRM, 9remote (documentados en PORTFOLIO.md).

## Acción crítica pendiente del usuario (ANTES del teardown)
1. **Guardar la passphrase del bundle** en lugar seguro (sin ella el bundle es irrecuperable).
2. **Sacar el bundle de la instancia**: descargar `backups/hermes-portfolio-state-*.tar.gz.gpg`
   vía filebrowser (files.el80.space) o confirmar que el rsync a la droplet DO (104.236.74.0) lo copió.
   La instancia se destruye → si el bundle no sale de la máquina, se pierde.

## Para reconstruir
Seguir `RECONSTRUCCION.md` paso a paso en el VPS nuevo.
