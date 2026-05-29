# Manual de instalación — Hermes Stack

> Guía completa para levantar el Hermes Stack **desde cero** en un VPS nuevo.
> Escrita para hacerse paso a paso, copiando y pegando. No hace falta saber programar.
>
> ¿Solo quieres el resumen rápido? Ver `RECONSTRUCCION.md`. ¿Qué contiene el portafolio? Ver `PORTFOLIO.md`.

---

## Antes de empezar — qué necesitas

| Cosa | Para qué |
|---|---|
| Un **VPS con Ubuntu 24.04** (mín. 4 GB RAM, 2 vCPU, 40 GB disco) | Donde corre todo |
| La **IP pública** del VPS y acceso SSH como `root` | Para conectarte |
| El dominio **el80.space** (o el tuyo) con acceso al panel DNS | Para los subdominios + HTTPS |
| El **bundle de estado cifrado** (`hermes-portfolio-state-*.tar.gz.gpg`) + su **passphrase** | Secretos, memoria y conocimiento |
| Las **API keys** (OpenRouter, Gemini, ElevenLabs) | Si no las tienes en el bundle |

> 💡 **Móvil:** puedes hacer todo desde la app **Termux** (Android) o cualquier cliente SSH.
> Conéctate con: `ssh root@TU_IP_DEL_VPS`

---

## Paso 1 — Apuntar el DNS

En el panel de tu proveedor de dominio, crea estos registros **A** apuntando a la IP del VPS:

```
hermes.el80.space     A   →  TU_IP
litellm.el80.space    A   →  TU_IP
router.el80.space     A   →  TU_IP
docs.el80.space       A   →  TU_IP
grafana.el80.space    A   →  TU_IP
files.el80.space      A   →  TU_IP
metrics.el80.space    A   →  TU_IP
```

> Opcionales (solo si vas a usar esos servicios): `livesync`, `crm`, `syncthing`.
> El HTTPS se genera solo (Let's Encrypt vía Caddy) una vez que el DNS apunta bien.
> Detalle de DNS/SSL: `docs/rules/infra-externa.md`.

---

## Paso 2 — Preparar el servidor (base + Docker + firewall)

Conéctate por SSH y trae el código:

```bash
cd /root
git clone https://github.com/erikjosehrnndz-crypto/hermes-stack.git .
```

> Si el repo tiene la rama del portafolio en vez de `main`:
> `git clone -b portfolio/teardown-2026-05-29 https://github.com/erikjosehrnndz-crypto/hermes-stack.git .`

Ejecuta el bootstrap (instala Docker, firewall UFW, fail2ban y dependencias):

```bash
sudo bash infra/bootstrap-server.sh
```

Instala el reverse proxy Caddy (gestiona el HTTPS automático):

```bash
sudo bash infra/setup-caddy.sh
```

**Verifica:**

```bash
docker --version           # debe imprimir una versión
systemctl status caddy     # debe decir "active (running)"
ufw status                 # 22, 80, 443 permitidos
```

---

## Paso 3 — Restaurar secretos y conocimiento (bundle Tier 2)

Sube el bundle cifrado al VPS (con filebrowser, `scp`, o descargándolo desde Drive con `wget`).
Déjalo en `/root/backups/`. Luego descífralo:

```bash
cd /root
gpg -d backups/hermes-portfolio-state-*.tar.gz.gpg > /tmp/state.tar.gz
# ↑ te pedirá la PASSPHRASE que guardaste
mkdir -p /tmp/state && tar xzf /tmp/state.tar.gz -C /tmp/state --strip-components=1
```

Restaura los **secretos** (incluye el `.env` con todas las API keys):

```bash
cp /tmp/state/secrets/.env /root/.env
cp -r "/tmp/state/secrets/Wallet_NEXUSMEMORY" /root/      # credenciales Oracle
cp /tmp/state/secrets/ruvector.db /root/ruvector.db
cp /tmp/state/secrets/filebrowser.db /root/filebrowser.db
```

Restaura el **estado del agente** y la **memoria de Claude**:

```bash
tar xzf /tmp/state/agent-state/hermes-state.tar.gz -C /root
mkdir -p /root/.claude/projects/-root
cp -r /tmp/state/claude-harness/memory /root/.claude/projects/-root/memory
```

Restaura el **conocimiento del brain** (vault + búsqueda + grafo):

```bash
for v in brain_vault brain_lance brain_graph; do
  docker volume create root_$v
  docker run --rm -v root_$v:/data -v /tmp/state/volumes:/b alpine \
    sh -c "tar xzf /b/root_$v.tar.gz -C /data"
done
```

> 🧠 Los **modelos de IA** del brain (1.8 GB) NO están en el bundle: se descargan solos
> la primera vez que arranca el brain. La primera consulta tardará unos minutos; es normal.

---

## Paso 4 — Si NO tienes el bundle (instalación limpia)

Si vas a empezar sin estado previo, en vez del Paso 3 crea el `.env` a mano:

```bash
cp /root/.env.template /root/.env
nano /root/.env          # rellena cada CAMBIA-ESTO con tu valor real
```

Claves obligatorias para arrancar: `LITELLM_MASTER_KEY` (invéntala, formato `sk-litellm-...`),
`OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`, `BRAIN_API_TOKEN`,
`ROUTER_JWT_SECRET`, `ROUTER_INITIAL_PASSWORD`, `COUCHDB_PASSWORD`, `FILEBROWSER_PASSWORD`.

---

## Paso 5 — Levantar el stack

```bash
cd /root
docker compose up -d --build
```

> La primera vez tarda (compila hermes, brain y website, y descarga imágenes).
> Paciencia — entre 5 y 15 minutos según el VPS.

(Opcional) Instala los servicios systemd de auto-curación:

```bash
sudo cp infra/docker-watchdog.service infra/docker-iptables.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now docker-watchdog docker-iptables
```

---

## Paso 6 — Verificar que todo funciona

```bash
docker compose ps        # TODOS deben decir "Up" / "healthy"
make health-check        # hermes OK · litellm OK
make doctor              # diagnóstico completo en 6 pasos
```

Prueba el **pipeline de voz** de extremo a extremo:

```bash
curl -X POST http://127.0.0.1:3001/api/voice -d '{"text":"hola"}'
# Respuesta esperada:
# {"text":"...","model_used":"gemini-flash","latency_ms":...}
```

Desde el navegador del móvil, comprueba los subdominios:
- `https://docs.el80.space` → web
- `https://files.el80.space` → gestor de archivos
- `https://grafana.el80.space` → métricas

---

## Paso 7 (opcional) — Servicios extra

```bash
# Panel de control + Obsidian LiveSync (sync de notas con el móvil)
docker compose -f docker-compose.yml -f docker-compose.optional.yml up -d

# Twenty CRM (contactos/empresas en crm.el80.space)
cd /root/twenty && docker compose up -d
```

---

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `make health-check` dice `litellm DOWN` | Falta o está mal una API key en `.env`. Revisa `OPENROUTER_API_KEY`/`GEMINI_API_KEY` y reinicia: `docker compose restart litellm` |
| HTTPS no funciona / "certificado inválido" | El DNS aún no apunta o no propagó. Espera y revisa `systemctl status caddy`; mira logs con `journalctl -u caddy -n 30` |
| Un contenedor reinicia en bucle | `docker compose logs --tail=50 NOMBRE` para ver el error |
| Brain tarda mucho en la 1ª consulta | Normal: está descargando los modelos (1.8 GB). Espera a que termine |
| `git push` pide usuario/contraseña | Usa el patrón con token de `docs/rules/git.md` (usuario `erikjosehrnndz-crypto`) |
| Healthcheck falla aunque el servicio responde | Usa `127.0.0.1`, no `localhost`, en los checks (ya está así en el repo) |

---

## Comandos del día a día

```bash
docker compose ps                       # estado de los servicios
docker compose logs -f hermes           # ver logs en vivo
docker compose restart hermes           # reiniciar un servicio
docker compose up -d --build website    # reconstruir tras un cambio
make backup                             # backup completo → /root/backups + droplet DO
make doctor                             # diagnóstico general
```

---

*Para entender la arquitectura completa: `README.md`, `docs/blueprint.txt` y el `wiki/`.*
