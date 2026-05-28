# Obsidian móvil con Self-hosted LiveSync

Guía completa para usar el vault de Obsidian del Hermes Stack desde el móvil con sincronización real-time bidireccional.

## Estado del backend

- **Servicio**: `couchdb-obsidian` (puerto `127.0.0.1:5984`).
- **Expuesto en**: `https://livesync.el80.space` (TLS automático vía Caddy + Let's Encrypt).
- **Usuario admin**: `obsidian`.
- **Password**: `$COUCHDB_PASSWORD` en `/root/.env` — copiar al gestor de contraseñas personal.
- **DBs**: `_users`, `_replicator`, `obsidian_vault`.
- **CORS habilitado** para `app://obsidian.md` y `capacitor://localhost` (requerido para móvil).
- **Health**: `make health-check` incluye CouchDB.
- **Backup**: el volumen `root_couchdb_data` se incluye automáticamente en `make backup`.

## Paso 1 — Migración inicial del vault al móvil (sin desktop)

El vault tiene 35 notas `.md` en `/var/lib/docker/volumes/root_brain_vault/_data/notes`. Como no hay Obsidian Desktop, hay que pasar esos archivos al móvil por otra vía. Recomendado:

### Opción A — Filebrowser ZIP (más simple, sin apps extras)

1. Entra a `https://files.el80.space` en el móvil (filebrowser).
2. Navega al path del vault (puede que esté en `/srv/var/lib/docker/volumes/root_brain_vault/_data/notes` o que necesites añadir el path como root del filebrowser).
3. Selecciona todos los `.md` → "Download" → genera ZIP.
4. Extrae el ZIP con una app de archivos (RAR, Files, etc.) en una carpeta del móvil, por ejemplo `Documents/vault/`.

### Opción B — Syncthing one-shot

1. Instala app **Syncthing-Fork** (Android, F-Droid o Play Store) o **Mobius Sync** (iOS).
2. En el VPS, levanta un servicio Syncthing temporal apuntando al path del vault (o añade el volumen como folder en un Syncthing ya existente).
3. Acepta el folder en el móvil → descarga los `.md` a un directorio local.
4. Una vez completado, **desinstala Syncthing del móvil** — ya no se necesita.

## Paso 2 — Instalar y abrir Obsidian móvil

1. Instala **Obsidian** desde Play Store / App Store (oficial, gratis).
2. Abre la app → "Create new vault" o "Open folder as vault".
3. Selecciona la carpeta donde extrajiste los 35 `.md` (paso 1).
4. Nombre del vault: cualquiera (sugerido: `hermes-vault`).

## Paso 3 — Instalar el plugin Self-hosted LiveSync

1. En Obsidian móvil → **Settings (⚙️)** → **Community plugins**.
2. Tap **Turn on community plugins** y acepta el warning "Use at your own risk".
3. Tap **Browse** → buscar `Self-hosted LiveSync` (autor: vorotamoroz).
4. Tap **Install** → **Enable** después de instalado.

## Paso 4 — Configurar LiveSync con CouchDB

1. Settings → **Self-hosted LiveSync** (debería aparecer en el menú izquierdo).
2. En **Setup Wizard** o **Remote Configuration**:
   - **URI**: `https://livesync.el80.space`
   - **Username**: `obsidian`
   - **Password**: el valor de `COUCHDB_PASSWORD` del VPS
   - **Database name**: `obsidian_vault`
3. Tap **Test Database Connection** → debe responder `Connected`.
4. **End-to-End encryption**: actívalo y define una passphrase fuerte. **Guárdala en el gestor de contraseñas — sin ella los datos en CouchDB son ilegibles si pierdes el dispositivo**.
5. Tap **Apply settings**.

## Paso 5 — Primera replicación

1. En Settings → LiveSync → **Replication**: tap **Initialize remote database**.
2. Confirma "send local data to remote" → sube los 35 `.md` a CouchDB.
3. Activa **LiveSync** (toggle en la parte superior) — desde ahora cualquier cambio es bidireccional en tiempo real.

## Paso 6 — Instalar pack SOTA de plugins

Desde Obsidian móvil → Settings → Community plugins → Browse → buscar e instalar cada uno. Activar tras instalar.

| Plugin | Funciona en móvil | Función |
|---|---|---|
| Self-hosted LiveSync | ✅ | Sync real-time (ya instalado) |
| Smart Connections | ✅ | Búsqueda semántica + AI |
| Omnisearch | ⚠️ parcial | Búsqueda full-text con scoring |
| Excalidraw | ✅ | Diagramas y sketches |
| Juggl | ❌ desktop-only | Se instala pero solo activo en desktop futuro |
| Dataview | ⚠️ degrada | Queries SQL-like sobre frontmatter |
| QuickAdd | ⚠️ parcial | Captura rápida con plantillas |
| Periodic Notes | ✅ | Daily/weekly notes |
| Templater | ✅ | Plantillas con lógica |
| Minimal Theme + Style Settings | ✅ | UI limpia y customizable |

Tip: LiveSync propaga la lista de plugins activos a futuros dispositivos. Si más adelante instalas Obsidian Desktop, basta con configurar LiveSync con las mismas credenciales y todo se descarga automáticamente.

## Verificación end-to-end

Crea una nota desde el móvil → en el VPS:

```bash
set -a && source /root/.env && set +a
curl -s -u obsidian:$COUCHDB_PASSWORD https://livesync.el80.space/obsidian_vault | jq '.doc_count'
```

El `doc_count` debe subir después de cada cambio sincronizado.

## Resolución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| "Connection failed" en Test Database | CORS / URI mal | Verificar `curl -H "Origin: app://obsidian.md" -I https://livesync.el80.space/` devuelve `access-control-allow-origin: app://obsidian.md` |
| "401 Unauthorized" | password incorrecta | Re-leer `COUCHDB_PASSWORD` en `.env`, no incluir espacios |
| Sync lento o queda colgado | demasiados chunks pequeños | Settings → Advanced → "Batch Size" 50 → "Batch Limit" 40 |
| Conflicto entre dispositivos | edición simultánea | LiveSync resuelve a nivel chunk; ante conflictos abrir el archivo con sufijo `~conflicted-...` |

## Recovery

Si CouchDB se rompe:

1. Restaurar el último `vol-root_couchdb_data-*.tar.gz` de `/root/backups/`:
   ```bash
   docker compose stop couchdb-obsidian
   docker volume rm root_couchdb_data
   docker volume create root_couchdb_data
   docker run --rm -v root_couchdb_data:/data -v /root/backups:/backup alpine sh -c "cd /data && tar xzf /backup/vol-root_couchdb_data-<TS>.tar.gz --strip-components=1"
   docker compose up -d couchdb-obsidian
   ```
2. La passphrase de E2E es la misma → el contenido se descifra al volver a conectar.

Si pierdes el dispositivo y la passphrase: los datos en CouchDB son ilegibles. Por eso `make backup` también guarda los `.md` originales del volumen `brain_vault` — son recuperables aunque el sync esté E2E-encriptado.
