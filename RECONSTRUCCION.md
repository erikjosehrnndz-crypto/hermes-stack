# RECONSTRUCCIÓN — levantar el Hermes Stack en una instancia nueva

> Runbook **manual**. Para el inventario completo, ver `PORTFOLIO.md`.
> Necesitas: (1) este repo, (2) el bundle de estado cifrado + su passphrase.

---

## 0. Requisitos en el VPS nuevo (Ubuntu 24.04)

Instala base con el script incluido (Docker + Caddy + firewall + fail2ban):

```bash
sudo bash infra/bootstrap-server.sh   # apt, Docker, ufw, fail2ban
sudo bash infra/setup-caddy.sh        # Caddy + despliega infra/Caddyfile
```

Apunta el DNS de `*.el80.space` a la IP nueva (ver `docs/rules/infra-externa.md`).

---

## 1. Traer el código (Tier 1)

```bash
cd /root
git clone https://github.com/erikjosehrnndz-crypto/hermes-stack.git .
```

---

## 2. Restaurar secretos y conocimiento (Tier 2)

Copia el bundle cifrado al VPS (vía filebrowser, scp o Google Drive) y descífralo:

```bash
cd /root
gpg -d backups/hermes-portfolio-state-*.tar.gz.gpg > /tmp/state.tar.gz   # pide la passphrase
mkdir -p /tmp/state && tar xzf /tmp/state.tar.gz -C /tmp/state --strip-components=1

# Secretos
cp /tmp/state/secrets/.env /root/.env
cp -r "/tmp/state/secrets/Wallet_NEXUSMEMORY" /root/
cp /tmp/state/secrets/ruvector.db /root/ruvector.db
cp /tmp/state/secrets/filebrowser.db /root/filebrowser.db

# Auth de 9router (tokens OAuth) — restaurar a .9router/ tras el primer up si aplica
# Estado del agente y memoria Claude
tar xzf /tmp/state/agent-state/hermes-state.tar.gz -C /root
mkdir -p /root/.claude/projects/-root && cp -r /tmp/state/claude-harness/memory /root/.claude/projects/-root/memory
```

Restaura los **volúmenes de conocimiento** del brain (vault/lance/graph) — crea los volúmenes
y vuelca cada tarball:

```bash
for v in brain_vault brain_lance brain_graph; do
  docker volume create root_$v
  docker run --rm -v root_$v:/data -v /tmp/state/volumes:/b alpine \
    sh -c "tar xzf /b/root_$v.tar.gz -C /data"
done
```

> Los **modelos** del brain (1.8 GB) NO están en el bundle: se descargan solos de HuggingFace
> en el primer arranque (`intfloat/multilingual-e5-large`). La primera consulta tardará más.

---

## 3. Levantar el stack núcleo

```bash
cd /root
docker compose up -d --build      # 14 servicios del Tier 1
```

---

## 4. Verificar

```bash
docker compose ps                 # todos Up/healthy
make health-check                 # hermes + litellm + (couchdb si aplica)
make doctor                       # diagnóstico completo (6 pasos)
```

Prueba de extremo a extremo del pipeline de voz:

```bash
curl -X POST http://127.0.0.1:3001/api/voice -d '{"text":"test"}'
# espera: {"text":"...","model_used":"gemini-flash","latency_ms":...}
```

Prueba de conocimiento (confirma que la memoria del brain viajó bien): usa la herramienta
MCP `brain_recall` y verifica que devuelve memoria previa.

---

## 5. (Opcional) Servicios Tier 3

```bash
# hermes-workspace + Obsidian LiveSync
docker compose -f docker-compose.yml -f docker-compose.optional.yml up -d
# Twenty CRM
cd /root/twenty && docker compose up -d
```

---

## Notas

- **Push git** desde el VPS: ver `docs/rules/git.md` (HTTPS con token incrustado, usuario `erikjosehrnndz-crypto`).
- `config/couchdb/local.ini` se auto-genera con UUID/hash al arrancar CouchDB — parte del `.template`.
- El bundle de estado es **secreto** (contiene `.env` + credenciales Oracle). Guárdalo cifrado; no lo subas a git.
