# SESSION_HANDOFF — 2026-05-29 → próxima sesión

## Estado: sin trabajo de código bloqueado. Pendiente acción manual del usuario + decisión de teardown.

Rama: `main` — último commit `809341a` (router refactor).

## Hecho esta sesión
- **CLAUDE.md → router lean** (`809341a`): 39863 → 6926 chars. Reglas universales + tabla de routing; detalle por dominio en `docs/rules/*.md` (12 módulos), cargado bajo demanda con `Read`. Reglas nuevas van al módulo, no a CLAUDE.md.
- **Obsidian Sync (oficial, plan Plus)**: el usuario lo compró. Migración previa por Syncthing (35 .md → móvil) ya completada en sesión anterior.

## Pendiente — acción del usuario (no es código)
1. **Vincular Obsidian Sync en el móvil**: login en cuenta → Settings→Sync→Create vault `hermes-vault` → passphrase E2E → Start syncing. Solo lo puede hacer él desde la app. Aún no lo hizo ("compré sync, todavía no vinculo").

## Pendiente — decisión de teardown (espera confirmación del usuario)
La infra self-hosted LiveSync quedó **dormida** tras elegir Obsidian Sync. NO borrar sin confirmación ("ya vinculé"):
- `couchdb-obsidian` (parado, volumen `root_couchdb_data` + `config/couchdb/local.ini` intactos).
- Bloque `livesync.el80.space` en `/etc/caddy/Caddyfile` y `/root/infra/Caddyfile`.
- Folder Syncthing `obsidian-vault` + `/root/Sync/obsidian-vault/` (35 .md).
- Health check de CouchDB en Makefile + backup de `root_couchdb_data`.

**Nota clave:** Obsidian Sync (oficial) NO puede correr en el VPS headless. Si el usuario quiere que el móvil sincronice con el vault del VPS que leen Hermes/brain, hay que volver a LiveSync — no a Obsidian Sync.

## siguiente paso recomendado
Esperar al usuario: o "ya vinculé" → ejecutar teardown de la infra LiveSync/Syncthing dormida; o reporte de problema con Obsidian Sync → reactivar `docker compose up -d couchdb-obsidian` (volumen intacto).
