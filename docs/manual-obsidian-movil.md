# Manual — Obsidian del móvil ↔ Hermes (Self-hosted LiveSync)

Cómo tener tus notas en el móvil **conectadas con el cerebro (brain) de Hermes**, sin
depender de la nube de Obsidian. Funciona con tu propio servidor.

## Cómo funciona (resumen)

```
Móvil (Obsidian + plugin Self-hosted LiveSync)
   │  vault "el80vault": tus notas personales + una carpeta brain/
   ▼  HTTPS  →  https://livesync.el80.space  (servidor CouchDB)
CouchDB (el80vault)
   ▲  solo la carpeta brain/
livesync-bridge  (puente automático en el servidor)
   ▼
vault del cerebro de Hermes  (lo leen brain / brain-worker)
```

- Lo que escribas en **cualquier carpeta** del móvil queda guardado en tu servidor (privado).
- Lo que pongas dentro de la carpeta **`brain/`** va al cerebro de Hermes, y lo que el
  agente genere aparece ahí en tu móvil. **Bidireccional.**
- Tu suscripción **Obsidian Sync (Plus)** NO se usa aquí: el Sync oficial no puede
  conectarse al servidor (no tiene pantalla). Esto la sustituye con algo autohospedado.

---

## Parte 1 — En tu móvil Android (lo que haces tú)

1. Instala **Obsidian** desde Google Play. Ábrelo y crea un vault nuevo llamado **`el80vault`**.
2. **Ajustes (⚙️) → Community plugins → Turn on community plugins.**
3. **Browse**, busca **"Self-hosted LiveSync"**, **Install** y luego **Enable**.
4. Abre los ajustes del plugin → sección **🛰️ Setup → Remote Database Configuration**:
   - **URI:** `https://livesync.el80.space`
   - **Database name:** `el80vault`
   - **Username:** `obsidian`
   - **Password:** *(la contraseña de CouchDB — está en `/root/.env`, variable `COUCHDB_PASSWORD`)*
   - **End-to-End Encryption:** **OFF** (déjalo desactivado).
   - Pulsa **Test Database Connection** → debe ponerse **verde / "Connected"**.
5. Pulsa **Check database configuration** → si ofrece arreglar algo (**Fix**), acéptalo.
6. En **Sync Settings** elige el modo **LiveSync** (sincronización en tiempo real) y pulsa
   **Apply**. Cuando lo pida, **recarga Obsidian**.
7. Espera unos segundos: aparecerá la carpeta **`brain/`** con las notas del cerebro de Hermes.

### Prueba rápida
- Crea una nota dentro de `brain/` (ej. `brain/hola.md`). En segundos estará en el servidor.
- El resto de carpetas (fuera de `brain/`) son tuyas y privadas; no tocan al agente.

---

## Parte 2 — Servidor (referencia técnica, ya desplegado)

Infra revivida desde el estado "dormido" + pieza nueva `livesync-bridge`.

### Servicios (en `docker-compose.optional.yml`, Tier-3 revivible)
```bash
# Levantar todo lo opcional (couchdb + bridge):
docker compose -f docker-compose.yml -f docker-compose.optional.yml up -d
```
- `couchdb-obsidian` (couchdb:3.3) → `127.0.0.1:5984`, expuesto por Caddy en
  `livesync.el80.space`. Config en `config/couchdb/local.ini`.
- `livesync-bridge` → puente headless CouchDB↔filesystem. Sincroniza la carpeta `brain/`
  de la DB `el80vault` con el volumen `root_brain_vault` (`/data/vault`).

### Reconstrucción del puente (no versionado; se clona en el rebuild)
`integrations/livesync-bridge/` está en `.gitignore` (es un repo externo). Para rehacerlo:
```bash
cd /root/integrations
git clone https://github.com/vrtmrz/livesync-bridge
cd livesync-bridge && git submodule update --init --recursive
# Parche Dockerfile (Deno 2.3.x): cambiar  `RUN deno install -A`
#   por  `RUN deno install --entrypoint main.ts`
```
Crear `integrations/livesync-bridge/dat/config.json` (el password real va aquí, fuera de git):
```json
{
  "peers": [
    { "type": "couchdb", "name": "remote-el80vault", "group": "g-brain",
      "url": "http://couchdb-obsidian:5984", "database": "el80vault",
      "username": "obsidian", "password": "<COUCHDB_PASSWORD>",
      "passphrase": "", "obfuscatePassphrase": "", "baseDir": "brain/",
      "useRemoteTweaks": true, "customChunkSize": 100, "minimumChunkSize": 20 },
    { "type": "storage", "name": "brain-vault", "group": "g-brain",
      "baseDir": "/data/vault/", "scanOfflineChanges": true, "useChokidar": true }
  ]
}
```
Luego: `docker compose -f docker-compose.yml -f docker-compose.optional.yml up -d --build livesync-bridge`

### Preparación de CouchDB (una vez, ya hecho)
```bash
# Tweaks runtime de LiveSync (idempotente):
curl -s https://raw.githubusercontent.com/vrtmrz/obsidian-livesync/main/utils/couchdb/couchdb-init.sh \
  | env hostname=http://127.0.0.1:5984 username=obsidian password="$COUCHDB_PASSWORD" bash
# Crear la base de datos del vault:
curl -X PUT -u obsidian:$COUCHDB_PASSWORD http://127.0.0.1:5984/el80vault
```

### Nota sobre el backlog inicial
`livesync-bridge` con `scanOfflineChanges` fija una **línea base** al arrancar y solo sube
cambios posteriores. Para empujar notas ya existentes una primera vez:
```bash
find /var/lib/docker/volumes/root_brain_vault/_data -name '*.md' -exec touch {} +
```
Las escrituras nuevas del `brain-worker` se detectan solas (chokidar). No hace falta repetirlo.

### Verificación
```bash
PW=$COUCHDB_PASSWORD
curl -fsS -u obsidian:$PW http://127.0.0.1:5984/_up                 # {"status":"ok"}
curl -fsS -u obsidian:$PW https://livesync.el80.space/el80vault      # JSON de la DB
docker logs livesync-bridge --tail 20                               # "Database is now ready."
```

### Activar cifrado E2E más adelante (opcional)
En el plugin del móvil pon una **passphrase** y deja la ofuscación de rutas en **OFF**.
Pon **la misma** passphrase en `dat/config.json` (campo `passphrase`) y reinicia el bridge.
Si las passphrases no coinciden, deja de sincronizar.
