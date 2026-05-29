# Integraciones nuevas — 29 mayo 2026

Resumen para Erik de los proyectos integrados en el Hermes Stack en esta sesión, cómo usarlos
desde el móvil, y qué se descartó.

---

## 1. codegraph — Claude Code entiende tu código sin gastar tokens

**Qué es:** una herramienta que indexa todo tu código en un "mapa" (grafo) y se lo da a
Claude Code como servidor **MCP**. Así Claude responde preguntas sobre la arquitectura sin
tener que abrir y leer archivos uno a uno → **~35% menos tokens y ~71% menos pasos**.

**Estado:** instalado y conectado. Índice ya construido sobre `/root`:
1.096 archivos · 21.104 nodos · 46.260 relaciones.

**Cómo se usa:** automático. Cuando hablas con Claude Code, ya tiene acceso a las
herramientas `codegraph` (aparecen como `mcp__codegraph__*`). No tienes que hacer nada.

**Mantenimiento (opcional):** tras cambios grandes en el código, refrescar el índice:
```bash
cd /root && codegraph sync
```
El índice vive en `/root/.codegraph/` (no se sube a git; pesa ~47 MB).

---

## 2. Understand-Anything — comandos `/understand` en Claude Code

**Qué es:** un **plugin de Claude Code** que analiza un proyecto con varios agentes, construye
un grafo de conocimiento (archivos, funciones, dependencias, flujos de negocio) y te lo
explica. Complementa a codegraph (codegraph = mapa rápido; Understand-Anything = explicación
guiada visual).

**Estado:** plugin instalado (`understand-anything@understand-anything`, scope usuario).

**Cómo se usa:** en Claude Code, escribe alguno de estos comandos:
- `/understand` — analiza el proyecto y construye el grafo.
- `/understand-dashboard` — abre el panel visual interactivo.
- `/understand-chat` — pregunta al código en lenguaje natural.
- `/understand-domain` — extrae los procesos de negocio.
- `/understand-explain`, `/understand-onboard`, `/understand-diff`, `/understand-knowledge`.

> Nota: estos comandos aparecen tras **reiniciar Claude Code** (cerrar y volver a abrir la
> sesión), porque los plugins se cargan al arrancar.

---

## 3. Twenty — tu CRM (gestión de contactos/empresas)

**Qué es:** un CRM open-source (alternativa libre a Salesforce) para guardar contactos,
empresas, oportunidades y tareas.

**Cómo entrar:** desde el móvil, abre **https://crm.el80.space**. La primera vez te pedirá
crear la cuenta de administrador (tu email + una contraseña). A partir de ahí, todo desde el
navegador.

**Detalles técnicos (por si hay que tocar):**
- Corre en 4 contenedores propios (`server`, `worker`, `db` Postgres, `redis`), separados del
  resto del stack para no interferir.
- Carpeta: `/root/twenty/`. Versión fijada: `v2.8.3`.
- Puerto interno `3005` (el 3000 ya lo usa Grafana; el 3002 el workspace).
- Secretos en `/root/twenty/.env` (NO se sube a git). ⚠️ **No borres `ENCRYPTION_KEY`**: si lo
  pierdes, pierdes el acceso a todos los datos cifrados del CRM.

**Operación:**
```bash
cd /root/twenty
docker compose ps                      # ver estado
docker compose --env-file .env up -d   # arrancar
docker compose down                    # parar
docker compose pull && docker compose --env-file .env up -d   # actualizar versión
```

---

## 4. Warp — descartado ❌

**Qué es:** Warp es una **terminal de escritorio** (app gráfica, escrita en Rust, que usa la
GPU para dibujar la ventana).

**Por qué no se implementó:** no tiene modo "headless" ni un componente servidor que se pueda
autohospedar. Necesita una pantalla y un escritorio para funcionar. Tu servidor (VPS) no tiene
pantalla y tú trabajas solo desde el móvil → no hay forma de ejecutarla ni de que te sea útil
aquí. Decisión confirmada contigo.

Si algún día quieres una terminal en el móvil, la vía es Termux (ya configurado en
`scripts/setup-termux.sh`), no Warp.

---

## Dónde quedó cada cosa

| Pieza | Ubicación | Se sube a git |
|---|---|---|
| codegraph (binario) | global npm `@colbymchenry/codegraph` | — |
| codegraph (índice) | `/root/.codegraph/` | no (ignorado) |
| codegraph (MCP) | `~/.claude.json` (proyecto /root) | no |
| Understand-Anything | plugin Claude Code (`~/.claude/plugins/`) | no |
| Twenty (config) | `/root/twenty/docker-compose.yml` | **sí** |
| Twenty (secretos) | `/root/twenty/.env` | no (ignorado) |
| Caddy `crm.el80.space` | `/etc/caddy/Caddyfile` + `/root/infra/Caddyfile` | el del repo sí |
