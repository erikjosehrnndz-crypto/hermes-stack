# CLAUDE.md — Hermes Stack

Instrucciones específicas del proyecto para Claude Code.
Se cargan automáticamente en cada sesión sobre este repositorio (`/root`).

---

## Checklist de inicio de sesión

Al retomar una sesión, ejecutar en orden:

```bash
git status                    # cambios sin commitear
git log --oneline -5          # commits recientes
git branch                    # rama activa
docker compose ps             # estado del stack en producción
rm -f /tmp/claude_progress    # limpiar barra de progreso stale (evita barra corrupta)
cat /root/SESSION_HANDOFF.md 2>/dev/null   # handoff de sesión anterior (si existe)
cat /root/PENDIENTES.md | head -20         # tareas activas
```

Si hay cambios sin commitear de una sesión anterior: analizarlos, commitearlos o descartarlos **antes** de empezar trabajo nuevo.

### Protocolo de cierre de sesión

Al finalizar cualquier sesión de trabajo, en orden:

1. **Actualizar PENDIENTES.md** — actualizar `estado` del ítem trabajado; añadir `evidencia` si se resolvió
2. **Ejecutar `make health-check`** (o `curl -f http://127.0.0.1:8080/health`) — confirmar que el stack sigue sano
3. **Commitear todo el trabajo** — nunca dejar cambios sin commitear al cerrar
4. **Si hay trabajo incompleto:** copiar `.claude/templates/session-handoff.md` → `/root/SESSION_HANDOFF.md` y rellenar el "siguiente paso recomendado" con una instrucción concreta

Sin clock-out: cada sesión siguiente empieza diagnosticando el estado desde cero. Con clock-out: la siguiente sesión lee `SESSION_HANDOFF.md` y continúa en 2 minutos.

### Una tarea activa por sesión

Completar el ítem activo antes de empezar el siguiente:
- Si surge una tarea secundaria durante el trabajo: registrarla en PENDIENTES.md pero **no empezarla**
- Excepción: si la tarea activa bloquea por dependencia externa, se puede avanzar otro ítem de PENDIENTES.md
- Excepción 2: dentro de una tarea, lanzar múltiples sub-agentes en paralelo está permitido (ver "Orquestación jerárquica")

Previene: context switching que deja 3 tareas al 70% en lugar de 1 al 100%.

### Definition of Done — toda tarea

Una tarea está **done** cuando se cumplen los 4 criterios:

1. Implementación existe en código
2. Verificación ejecutada: no "debería funcionar" — correr el comando real de verificación
3. Evidencia registrada: commit hash o output del comando en PENDIENTES.md o SESSION_HANDOFF.md
4. Stack reiniciable: `docker compose ps` muestra todos los servicios Up

Si falta cualquier criterio: el ítem no está done aunque el código esté escrito.

### Verificación gate — `make check`

Todos los comandos de verificación están unificados en `/root/Makefile`:

```bash
make check        # build Next.js + health checks + lint Python
make build-check  # solo Next.js build
make health-check # solo health de servicios
make status       # docker compose ps
make logs         # logs recientes de hermes, litellm, website
```

Usar `make check` antes de declarar cualquier tarea completada.

---

## Git

### Push HTTPS — ÚNICO método que funciona en este VPS

El remote usa HTTPS, no SSH. El helper de credenciales git **no está configurado** en este VPS, por lo que `git push` falla con "could not read Username" si no se incrusta el token. Patrón obligatorio:

```bash
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
```

Restaurar la URL limpia después de cada push — el token no debe quedar en el remote URL.

**GitHub username:** `erikjosehrnndz-crypto` (con `-crypto`). No usar versiones sin el sufijo.

### .gitignore antes de `git add` en cualquier directorio nuevo

Antes de hacer `git add <dir>/`, hacer `ls -la <dir>` e identificar artefactos. Reglas específicas de este proyecto:

| Directorio | Ignorar |
|---|---|
| `hermes_bp/` | `*.aux *.toc *.out *.lot *.log *.synctex.gz *.db` |
| `website/` | `node_modules/ .next/ dist/ *.db` |
| cualquier Python | `__pycache__/ *.pyc .venv/` |

El `.gitignore` raíz tiene `.*` que ignora todos los dotfiles. Para que los `.gitignore` de subdirectorios funcionen, el raíz debe tener `!.gitignore` como excepción — ya está añadido.

**Consecuencia importante:** `git add` de cualquier dotfile (`.claude/`, `.env`, etc.) falla. Ver sección "`.claude/` está en `.gitignore`" en Claude Code — Configuración de permisos.

### `git add` siempre desde el directorio raíz `/root`

`git add docker-compose.yml` falla si el CWD no es `/root` (el raíz del repo). Patrón obligatorio:

```bash
cd /root && git add <archivo-relativo-al-repo>
# o bien usar la ruta desde raíz sin cd:
git -C /root add <archivo>
```

**Previene:** `fatal: pathspec 'X' did not match any files` cuando el shell está en un subdirectorio.

### Archivos que nunca van al repositorio

```
*.db              # filebrowser.db, ruvector.db — bases de datos runtime
*.zip             # backups y archivos de exportación
Sync/  snap/      # directorios del sistema
*.aux *.toc *.out *.lot *.log   # artefactos LaTeX
node_modules/  .next/  dist/    # dependencias y builds de frontend
.env  .env.*                    # secretos
```

### Verificar build antes de hacer commit

**Regla obligatoria:** antes de `git add` + `git commit` en cualquier cambio de frontend, ejecutar el build para confirmar que compila sin errores:

```bash
cd website && npm run build   # debe completar sin errores TS ni de compilación
```

Previene commits rotos que el CI detecta después. Si el build falla, corregir antes de commitear — nunca commitear con el build roto aunque "sea solo un cambio pequeño".

### Commit por tarea lógica, no por sesión

Commitear al finalizar cada tarea individual. No acumular cambios de múltiples tareas en un solo commit al final de la sesión — si la sesión cae por rate limit, el trabajo sin commit se pierde.

### Commit ANTES de lanzar orquestación multi-agente

Cualquier trabajo no commiteado antes de lanzar una ronda de sub-agentes se puede perder si el context limit ocurre durante la ejecución paralela.

**Regla:** `git commit` de todo el trabajo en curso ANTES de lanzar agentes de larga duración.
Previene: pérdida de trabajo entre sesiones por rate limit durante orquestación.

### Nombramiento de ramas

```
feat/<nombre>     # nueva funcionalidad
fix/<nombre>      # corrección de bug
docs/<nombre>     # cambios de documentación
chore/<nombre>    # mantenimiento (gitignore, CLAUDE.md, deps)
```

### Workflow de PR

```bash
git checkout -b feat/mi-feature
# ... trabajo y commits ...
# push usando patrón HTTPS con token (ver sección Git arriba)
gh pr create --title "..." --body "..."
```

---

## Edición de archivos

**Siempre leer el archivo completo antes de editar.** Nunca hacer `Edit` al final de un archivo sin haber leído las últimas líneas — puede haber contenido de sesiones anteriores que invalida el contexto.

```
1. Read <archivo> completo
2. Identificar secciones existentes
3. ¿Edición puntual?  → Edit
   ¿Más del 30% cambia? → Write con archivo completo
```

**No appendear secciones nuevas** si ya existe una sección equivalente — editar la existente. Causa de error pasado: sección CI/CD duplicada en README por append sin leer el final del archivo.

### Write tool exige Read tool — Bash cat no cuenta

El tool `Write` (para sobreescribir un archivo existente) requiere haber usado el tool `Read` en la misma sesión. Ver el contenido con `Bash cat` o `Bash head` **no satisface** ese requisito. Si se intenta `Write` sin `Read` previo: error "File has not been read yet".

```
❌ Bash(cat archivo.md) → Write(archivo.md)   # falla
✅ Read(archivo.md)    → Write(archivo.md)   # funciona
✅ Read(archivo.md)    → Edit(archivo.md)    # funciona
```

**Previene:** error "File has not been read yet". Antes de cualquier `Write` en archivo existente, verificar que hubo un `Read` del mismo archivo en este turno.

---

## Sub-agentes vs escritura directa

**Usar sub-agentes** cuando el contenido requiere investigación genuina en fuentes desconocidas o múltiples archivos que no están en contexto.

**Escribir directamente** cuando:
- El contenido fuente ya está en contexto o en un archivo conocido
- La tarea es convertir/reformatear algo existente (texto → LaTeX, etc.)
- La tarea es < 30 min de escritura directa

**Regla:** Si el contenido fuente ya existe → escribir directo. Solo paralelizar si la investigación genuinamente lo requiere y cada agente escribe su output a disco antes de terminar. N agentes con rate limit simultáneo = pérdida total si no hay archivos en disco.

### Checkpointing obligatorio en sub-agentes

Cada sub-agente que produzca contenido debe escribirlo a un archivo en disco (ej. `/tmp/<task_id>.md`) como **última acción antes de terminar** — no solo retornarlo en la respuesta del agente.
Previene: pérdida del 100% del trabajo cuando el orquestador choca con rate limit antes de recolectar resultados.

### Sub-agentes no heredan permisos Write/Bash del padre

Los sub-agentes lanzados con TaskCreate no heredan permisos Write/Bash del orquestador. Si un agente necesita escribir archivos o ejecutar comandos, el orquestador debe configurar `.claude/settings.json` antes de lanzarlo, o el orquestador debe escribir él mismo los archivos con los resultados.
Previene: ciclo de bloqueos de permisos que consume rate limit sin producir archivos.

### CLAUDE.md solo debe editarlo el agente principal

Los sub-agentes que editan `CLAUDE.md` reciben un security warning ("self-modification soft block") por ser un archivo que controla el comportamiento del agente. Patrón correcto:
1. Sub-agentes investigan y devuelven sus hallazgos como texto
2. El agente principal (orquestador) hace el `Edit`/`Write` final sobre `CLAUDE.md`

Previene: friction de warnings y posible bloqueo de edición desde sub-agentes.

### Síntesis incremental y contexto en sub-agentes

Con 4+ agentes en paralelo, lanzar síntesis de forma incremental (excepción: si necesita TODOS los inputs, esperar es correcto). Incrustar contexto necesario (MEMORY.md, CLAUDE.md) en los prompts — el orquestador no debe hacer Bash/Read sobre trabajo ya delegado.

### Economía de modelos en orquestación multi-agente

Asignar el modelo mínimo suficiente por fase:
- **Haiku:** lectura de archivos, extracción de datos, mapeo estructural
- **Sonnet:** síntesis, redacción técnica, generación de documentos
- **Opus:** orquestador raíz SIEMPRE (ver siguiente regla), o sub-agente si el usuario lo activa explícitamente


---

## Orquestación jerárquica con Opus 4.7

### El orquestador raíz SIEMPRE usa el mejor modelo disponible

Cualquier `/gg`, `/swarm`, plan multi-agente o tarea con sub-agentes **debe** ser orquestado por el modelo más potente disponible. **Actualmente: Opus 4.7** (`claude-opus-4-7`).

**Verificación al inicio de cualquier orquestación:**
1. Si el modelo activo no es Opus 4.7 (o el más potente del momento), avisar al usuario y sugerir `/model` antes de proceder.
2. El orquestador raíz **nunca** se degrada a Sonnet/Haiku — los modelos pequeños son SOLO para sub-agentes.

El orquestador toma decisiones de alto impacto; un modelo débil orquestando agentes fuertes produce decomposiciones torpes. Modelos pequeños → solo sub-agentes.

### Sub-agentes pueden lanzar sub-swarms — solo con autorización del padre

Un sub-agente que necesite paralelizar debe **retornar primero** su solicitud (razón, agentes propuestos, tokens estimados, outputs a `/tmp/`) — nunca lanzar directamente. El padre aprueba/rechaza antes de re-invocar. Profundidad máxima: 3 niveles. Toda autorización fluye top-down.

**Previene:** explosión de costes.

### Sub-agentes de larga duración → `run_in_background: true`

Cualquier sub-agente cuya tarea estimada exceda **60 segundos** debe lanzarse con `run_in_background: true`. El orquestador recibe notificación automática al completar, no debe `sleep` ni hacer polling.

**Regla práctica:** lectura simple → foreground · investigación/redacción → background · síntesis final → foreground.

### Plan jerárquico explícito al inicio del swarm

Antes de lanzar agentes, documentar la jerarquía: cada agente lleva rol, modelo (Haiku/Sonnet/Opus), modo (background/foreground) y dependencias de output. Sin este plan, los agentes quedan esperando inputs que nunca llegan.

---

## Dependencias — verificar versión antes de usar features

Antes de usar una característica específica de versión de cualquier librería, verificar la versión instalada:

```bash
cat node_modules/<lib>/package.json | grep '"version"' | head -1
# o bien:
npm list <lib>
```

**No asumir que la versión instalada soporta las últimas features.** El check de versión debe ser el **primer paso** cuando el plan menciona archivos de configuración version-específicos. Verificar primero, escribir después.

---

## Next.js / website

La carpeta `website/` usa **Next.js 14 App Router + TypeScript**. Versión instalada: 14.2.x.

### Archivo de configuración — `.mjs`, nunca `.ts`

Next.js 14.x **no** soporta `next.config.ts`. Solo Next.js 15+ lo soporta.

```
✓  next.config.mjs    ← usar siempre para Next.js 14
✗  next.config.ts     ← solo Next.js 15+, NO usar hasta actualizar
```

Error concreto si se usa `.ts` en v14:
```
Error: Configuring Next.js via 'next.config.ts' is not supported.
```

### App Router — `'use client'` en componentes con hooks

Todo componente que use `useState`, `useEffect`, `fetch`, `window`, `document` u otras APIs de browser **debe** tener `'use client'` como primera línea (antes de cualquier import):

```tsx
'use client';

import React, { useState, useEffect } from 'react';
```

Sin esta directiva, Next.js intenta renderizarlo en el servidor y lanza errores de hidratación o de módulos de browser no disponibles.

Aplica especialmente a `src/App.tsx` y cualquier componente en `src/components/` que use hooks.

### Dockerfile standalone — `public/` debe existir

El Dockerfile de Next.js standalone incluye:
```dockerfile
COPY --from=builder /app/public ./public
```

Si `public/` no existe en el repositorio, el Docker build **falla silenciosamente** o lanza error en la copia. Siempre crear `public/.gitkeep` si no hay assets estáticos:

```bash
mkdir -p website/public && touch website/public/.gitkeep
git add website/public/.gitkeep
```

### Estructura de archivos App Router

```
website/
├── app/
│   ├── layout.tsx          # Root layout — importa globals CSS, define metadata
│   ├── page.tsx            # Home page — renderiza App component
│   └── api/
│       ├── tree/route.ts   # GET /api/tree — árbol de directorios
│       └── health/route.ts # GET /health   — health check
├── src/
│   ├── App.tsx             # SPA principal ('use client')
│   ├── index.css           # Tailwind + custom styles
│   └── components/         # Componentes React ('use client' si usan hooks)
├── public/                 # Assets estáticos (.gitkeep si está vacío)
├── next.config.mjs         # Configuración Next.js (output: 'standalone')
├── tsconfig.json           # TypeScript para App Router
├── postcss.config.js       # Requerido por Tailwind en Next.js
└── tailwind.config.js      # content paths incluyen app/ y src/
```

### API Routes — Next.js Route Handlers vs Express

Los endpoints de API se implementan como Route Handlers en `app/api/*/route.ts`, no con Express. Patrón:

```ts
// app/api/ejemplo/route.ts
import { NextResponse } from 'next/server';
export async function GET() {
  return NextResponse.json({ data: 'valor' });
}
```

No añadir Express ni otros servidores HTTP — Next.js `next start` sirve tanto el frontend como las API routes.

### `force-dynamic` obligatorio en routes GET con datos en tiempo real

Next.js 14 cachea rutas `GET` por defecto en production build. Sin la directiva, `/api/metrics` y `/api/health` sirven datos stale. Añadir **como primera exportación** en cualquier route que devuelva datos dinámicos:

```ts
export const dynamic = 'force-dynamic';
```

El build confirma: rutas con la directiva muestran `ƒ (Dynamic)`, sin ella `○ (Static)` — señal de caché activa.

**Previene:** health check always-healthy aunque el servicio esté caído; métricas congeladas en producción.

### `.next/` — artefacto de build, nunca al repositorio

`.next/` es el directorio de output del build. Está en `.gitignore` raíz. Confirmar que esté ignorado antes de cualquier `git add` en `website/`.

---

## LaTeX / XeLaTeX

### Conflicto Babel español + TikZ — siempre aplicar

Con `\usepackage[spanish]{babel}`, el carácter `>` se vuelve activo y rompe `>=Stealth`. Error: `Package pgfkeys Error: I do not know the key '\par'`.

```latex
\usepackage{tikz}
\usetikzlibrary{babel,arrows.meta,positioning,calc,fit,backgrounds}
%               ^^^^^ babel PRIMERO en la lista, siempre
```

### YAML no existe en listings — definir en preámbulo

`\lstdefinelanguage{yaml}{...}` con `keywords`, `comment=[l]{\#}`, `morestring=[b]'` y `morestring=[b]"`. No está en los paquetes de listings por defecto.

### Fuentes disponibles en este VPS

```
DejaVu Serif / DejaVu Sans / DejaVu Sans Mono  ✓
fontawesome5                                    ✗  (no instalado)
```

No usar `\faIcon{}`. Sustituir con texto o Unicode directo.

### `\checkmark` requiere `amssymb`

`\checkmark` no está en el núcleo de LaTeX. Sin el paquete, compila con errores silenciosos y el símbolo queda vacío.

```latex
\usepackage{amssymb}   % añadir si se usa \checkmark o \square, \triangleright, etc.
```

**Previene:** error `! Undefined control sequence. \checkmark`.

### Compilación — 3 pasadas + verificación

```bash
xelatex -interaction=nonstopmode main.tex   # pasada 1
xelatex -interaction=nonstopmode main.tex   # TOC y labels
xelatex -interaction=nonstopmode main.tex   # outlines e hyperlinks
grep "^!" main.log | sort -u               # debe salir vacío
pdfinfo main.pdf | grep Pages              # verificar página count
```

---

## Slash commands globales (`~/.claude/commands/`)

### Directorio + /evolve — notas operativas

- `~/.claude/commands/` no existe por defecto — `mkdir -p` antes del primer slash command global.
- `/evolve` es **prospectivo**: reglas añadidas al cerrar sesión benefician la siguiente, no rescatan la actual.
- Transcripts multi-sesión en `/root/.claude/projects/-root/<sessionId>.jsonl`, índice en `/root/.claude/history.jsonl`.

### /plan con Ruflo disponible → proponer swarm desde el inicio

Si la tarea involucra investigación multi-dominio + síntesis, proponer swarm (Researcher / Memory Specialist / Reviewer / Coder) — no enfoque secuencial con bash.

### /plan con "SOTA" / "máximo esfuerzo" → WebSearch ANTES de diseñar

Trigger: "state of the art", "lo mejor", "máxima calidad", "máximo esfuerzo". Lanzar ≥2 Explore agents con WebSearch antes de diseñar — el conocimiento de entrenamiento tiene cutoff fijo y librerías líderes cambian (GraphRAG → LightRAG, etc.).
**Previene:** diseño obsoleto que requiere re-trabajo completo.

---

## CI/CD pipeline — referencia

GitHub Actions → SSH al VPS → `git pull /root` → `docker compose up -d --build` → health checks autenticados → **rollback automático a `HEAD~1` si el health check falla**.

Leer `.github/workflows/deploy.yml` antes de:
- Hacer push a `main`
- Modificar el workflow de deploy
- Cambiar health check endpoints

---

## Recursos de referencia del proyecto

- **Blueprint:** `/root/Hermes_Stack_Blueprint.pdf` (52 pp) — arquitectura completa. Leer antes de tareas de contexto profundo.
- **LaTeX base:** `main.tex + s1_*.tex + s2_*.tex + s3_*.tex + s4_*.tex` — compila limpio (24 pp). Usar como plantilla.

---

## Claude Code — Configuración de permisos

### Dos archivos, dos roles distintos

| Archivo | Rol | Origen |
|---|---|---|
| `~/.claude/settings.json` | Permisos **canónicos** del proyecto — editar manualmente | Commitear en memoria mental |
| `~/.claude/settings.local.json` | Acumulación automática de clicks "Allow" en el UI | **Limpiar periódicamente** |

**Regla:** toda operación regular del workflow de CLAUDE.md debe estar en `settings.json`. No esperar a que se acumule en `settings.local.json`.

### Permisos canónicos para este VPS (estado 2026-05-25)

Las siguientes reglas en `settings.json` cubren el workflow completo:

| Patrón | Cubre |
|---|---|
| `Bash(git *)` | Todas las operaciones git incluyendo push HTTPS con token |
| `Bash(gh *)` | GitHub CLI: auth, pr create, api, repo |
| `Bash(docker *)` | docker compose ps/up/down/logs/inspect |
| `Bash(curl *)` | Health checks post-deploy (`curl -f http://...`) |
| `Bash(npm *)` | npm install, run build, run dev, list |
| `Bash(xelatex *)` | Compilación LaTeX 3 pasadas |
| `Write(/root/website/*)` | Frontend Next.js |
| `Write(/root/hermes/*)` | Código del agente Python |
| `Write(/root/config/*)` | litellm.yaml y configs de servicios |
| `Write(/root/.claude/*)` | Hooks, settings, statusline |

### `.claude/` está en `.gitignore` — settings.json NO va al repositorio

El `.gitignore` raíz contiene `.*`, que ignora **todos los dotfiles**, incluyendo `.claude/`.
`git add .claude/settings.json` falla — este archivo **vive solo en el VPS**.

**Consecuencia:** si el VPS se reinicia o se clona el repo en otra máquina, hay que recrear `settings.json` manualmente a partir de la tabla de permisos canónicos de esta sección.

### Síntoma de acumulación — cuándo limpiar

```bash
cat ~/.claude/settings.local.json | jq '.permissions.allow | length'
```

Si > 20 reglas: revisar si alguna nueva necesita pasar a `settings.json`, luego limpiar:

```bash
echo '{}' > ~/.claude/settings.local.json
```

Previene: reglas específicas obsoletas, bugs de doble slash, y ruido que entierra permisos reales.

### Bug — doble slash en Read permissions

`Read(//usr/bin/**)` con doble slash es un bug silencioso — la regla no matchea nada. Ocurre cuando el permiso se concede via UI desde un path que el sistema pasa con `//`.

```
✓  Read(/usr/bin/**)          ← slash simple, funciona
✗  Read(//usr/bin/**)         ← doble slash, silently broken
```

Siempre verificar con `jq` después de cualquier consolidación:
```bash
jq '.permissions.allow[]' ~/.claude/settings.json | grep '//'   # debe salir vacío
```

---

## Docker — nombres de servicio vs contenedor

En este proyecto hay una distinción importante para `docker compose up --no-deps`:

| Servicio (`docker compose`) | Contenedor (`docker inspect`) |
|---|---|
| `litellm` | `litellm-router` |
| `hermes` | `hermes-agent` |
| `whisper-stt` | `whisper-stt` |

El watchdog y cualquier script que use `docker compose up --no-deps <servicio>` debe usar el **nombre de servicio**, no el nombre de contenedor.

### Docker healthcheck — usar `127.0.0.1`, no `localhost`

`localhost` en contenedores Alpine puede resolver a `[::1]` (IPv6) mientras el proceso escucha en IPv4 → `Connection refused` aunque el servicio esté up. Usar `127.0.0.1` siempre en healthchecks:

```yaml
test: ["CMD", "wget", "--spider", "http://127.0.0.1:3000/api/health"]  # ✓
```

**Previene:** healthcheck always-failing que oculta el estado real del contenedor.

---

## Stack de producción — referencia rápida

| Parámetro | Valor |
|---|---|
| Directorio raíz VPS | `/root` |
| Dominio base | `el80.space` |
| Repositorio | `github.com/erikjosehrnndz-crypto/hermes-stack` |
| Contenedores activos | 10 |
| Latencia E2E objetivo | < 500 ms |

### Mapa de servicios y puertos

| Servicio | Puerto host | Subdominio |
|---|---|---|
| hermes-agent | `127.0.0.1:8080` | `hermes.el80.space` |
| litellm-router | `127.0.0.1:4000` | `litellm.el80.space` |
| grafana | `127.0.0.1:3000` | `grafana.el80.space` |
| hermes-website | `127.0.0.1:3001` | `docs.el80.space` |
| filebrowser | `127.0.0.1:8095` | `files.el80.space` |
| whisper-stt | `127.0.0.1:9000` | — interno |
| prometheus | `127.0.0.1:9090` | — interno |

### Health check post-deploy

```bash
source /root/.env
curl -f -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
curl -f http://127.0.0.1:8080/health
```

Siempre verificar antes de declarar un deploy exitoso.

---

## Planificación interna implícita

El usuario **no** necesita escribir `/plan` para activar la planificación. Cualquier tarea no trivial — multi-paso, multi-archivo, multi-agente, con dependencias o riesgos — debe planificarse internamente **antes** de empezar a escribir o ejecutar.

**Regla:** planificación implícita, ejecución directa.

- Tareas triviales (un solo Edit puntual, un `git status`, una respuesta corta) → ejecutar sin plan.
- Tareas no triviales → construir el plan **internamente** (en thinking, no en output al usuario), luego ejecutar.
- Solo entrar en plan mode formal (`ExitPlanMode`) si el usuario lo pide explícitamente o si el riesgo de la decisión amerita su aprobación previa (cambios irreversibles, refactors grandes, deploys).

**Qué significa "planificar internamente":**
1. Identificar archivos a tocar y el orden.
2. Detectar dependencias entre pasos (qué bloquea a qué).
3. Decidir si requiere swarm (ver "Orquestación jerárquica con Opus 4.7") o escritura directa.
4. Verificar pre-condiciones (versión de librería, existencia de directorios, permisos).
5. Solo entonces empezar a ejecutar.

**Previene:** ciclos write → error → fix por saltarse el análisis.

---

## Estilo de comunicación — output mínimo

El usuario paga por cada token de output. La regla para esta sesión y todas las futuras es:

**No narrar el procedimiento ni el progreso.** Nada de "voy a hacer X", "ahora hago Y", "completado Z". El diff y los commits cuentan la historia — no la repitas en prosa.

**No mostrar el contenido completo de archivos editados** salvo petición explícita del usuario.

### La barra de progreso vive en la status line del sistema, no en el chat

La barra **no se imprime en el chat** — vive en la `statusLine` via hook `PostToolUse` + `statusline.sh`. Iniciar: `echo "0|<N_pasos>|<task>|0|$(date +%s)" > /tmp/claude_progress`. Auto-incrementa, auto-limpia al 100%.

### Reglas de implementación de la barra (para no romperla)

No usar `set -euo pipefail` · construir con string slicing no `seq` · detectar sub-agentes solo si hay archivo de progreso activo. **Previene:** barra en 0%, salida silenciosa.

**Regla del chat:** silencioso durante el trabajo. Excepciones: bloqueo real → mensaje claro · cierre de turno → UNA línea con commit hash · petición explícita → explicar.

---

## Sesiones de voz / remote-control

Los prompts dictados por micrófono llegan con errores de transcripción. Normalizar antes de procesar:

| Transcripción errónea | Interpretación correcta |
|---|---|
| `togen` | `tokens` |
| `pitline` | `pipeline` |
| `opus 4.7` | el modelo más potente disponible |
| `swcion` / `sewion` / `ression` | `sesión` |
| `backgraund` / `bacgraun` | `background` |
| `orwuestador` / `orquertador` | `orquestador` |
| `jerarqia` / `gerarquia` | `jerarquía` |
| `metrivas` / `metriques` | `métricas` |
| `sintodo` / `sintax` | `sintaxis` |

Ante ambigüedad: inferir la interpretación más razonable en el contexto del stack antes de pedir aclaración.

---

## Hermes Agent — patrones de performance (Python)

### aiohttp ClientSession — siempre compartida, nunca por request

Crear `aiohttp.ClientSession` en `start()` y cerrarla en `stop()` — **no dentro de `_query_llm`**. El patrón `async with aiohttp.ClientSession() as session:` por cada request abre y cierra una conexión TCP+TLS nueva cada vez, añadiendo ~50-200ms de overhead.

```python
async def start(self):
    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
    self._session = aiohttp.ClientSession(connector=connector)

async def stop(self):
    if self._session:
        await self._session.close()
```

Registrar `on_startup`/`on_cleanup` en el `aiohttp.web.Application`:
```python
app.on_startup.append(lambda app: app["agent"].start())
app.on_cleanup.append(lambda app: app["agent"].stop())
```
**Previene:** latencia extra por reconexión TCP en cada LLM call.

### Handlers externos — usar la sesión compartida del agente

Handlers en módulos separados deben recibir y usar `agent._session`, no crear `aiohttp.ClientSession()` propia. Patrón: `check_litellm(url, request.app["agent"]._session)` con fallback `async with aiohttp.ClientSession()` solo si `session is None or session.closed`.

**Previene:** overhead TCP+TLS en healthcheck (autoheal cada 30s = 2 conexiones efímeras/30s).

### orjson en lugar de json stdlib

`orjson` es drop-in (import orjson) y 3-10× más rápido. Diferencia de API:
- `orjson.dumps()` devuelve `bytes`, no `str`
- Para escritura en archivo: `f.write(orjson.dumps(obj) + b"\n")` — abrir en modo `"ab"` no `"a"`
- Para request HTTP con aiohttp: pasar `data=orjson.dumps(payload)` con `Content-Type: application/json` en headers (no usar el parámetro `json=`)

### cachetools.TTLCache para dedup de queries de voz

Whisper puede transcribir la misma frase dos veces en segundos si el micrófono captura eco. Un `TTLCache(maxsize=256, ttl=60)` con clave `hash(model+text)` previene doble gasto de tokens:

```python
from cachetools import TTLCache
self._query_cache: TTLCache = TTLCache(maxsize=256, ttl=60)
```

### LiteLLM Redis cache — activar desde el inicio

Redis ya corre en el stack. Añadir siempre a `config/litellm.yaml`:

```yaml
litellm_settings:
  cache: True
  cache_params:
    type: redis
    host: redis
    port: 6379
    ttl: 3600
```

Sin esto, queries LLM idénticas (misma sesión, mismo prompt) consumen tokens innecesariamente.

---

## Brain — retrieval pipeline

### FastEmbed: verificar modelo disponible antes de codificar

`BAAI/bge-m3` no está en fastembed 0.4.x. Modelo equivalente instalado (1024d, multilingüe): `intfloat/multilingual-e5-large`. Verificar lista real antes de commitear cualquier model_name:

```bash
docker compose exec brain-worker python3 -c \
  "from fastembed import TextEmbedding; [print(m['model']) for m in TextEmbedding.list_supported_models()]"
```

**Previene:** `ValueError: Model X is not supported in TextEmbedding` al primer deploy.

### RRF score ≠ similarity — exponer max(component_scores) como score de display

RRF = 1/(rrf_k+rank); máximo ≈ 0.016 con rrf_k=60. Usar RRF solo para ordenar hits. El campo `score` devuelto al caller debe ser `max(component_scores.values())` (cosine sim ∈ [0,1]).

**Previene:** acceptance tests con `score > 0.4` que fallan aunque el retrieval sea correcto.

### Embedded DBs — acceso multi-proceso

Antes de integrar una DB embedded en arquitectura API + worker, verificar soporte concurrente:
- **Kuzu** ❌ single-proceso — lanza "Could not set lock" si dos procesos abren el mismo archivo
- **SQLite WAL** ✅ multi-proceso — múltiples readers + 1 writer concurrentes
- **LanceDB** ⚠️ writes single — lecturas concurrentes OK

**Previene:** "Could not set lock on file" en workers cuando el proceso API ya tiene la DB abierta.

### fastembed TextCrossEncoder — devuelve floats, no objetos

`TextCrossEncoder.rerank(query, passages)` retorna `list[float]` (logits crudos) en el mismo orden que `passages`. Normalizar con sigmoid para [0,1]: `1.0 / (1.0 + math.exp(-score))`.

**Previene:** `AttributeError: 'float' object has no attribute 'document_id'`.

### try/except pass en workers — usar logging mínimo

`except: pass` en workers oculta errores críticos (locks de DB, permisos) y hace el debugging imposible. Mínimo aceptable: `except Exception as e: logging.warning("op failed: %s", e)`.

**Previene:** horas de debugging por errores silenciados (Kuzu lock era silenciado por `pass`).

### Servicios con imagen compartida — reconstruir TODOS al mismo tiempo

`brain` y `brain-worker` comparten Dockerfile y source. Un fix Python requiere: `docker compose build brain brain-worker`. Reconstruir solo uno deja el otro con el error anterior.

**Previene:** worker crasheando con error ya corregido mientras brain funciona.

### FastMCP 3.x — trailing slash obligatorio en URL del cliente

FastMCP 3.x redirige `/mcp` → `/mcp/` (307). Configurar siempre con trailing slash en `~/.claude.json` y en 9router:

```json
"url": "https://brain.el80.space/mcp/"
```

**Previene:** loop de redirección o fallo silencioso en clientes que no siguen redirects automáticamente.

### Claude Code — MCP en `~/.claude.json`, no en archivo separado

La key `mcpServers` vive en `~/.claude.json`. No existe `mcp.json` independiente. Formato HTTP Streamable:

```json
"mcpServers": { "brain": { "type": "http", "url": "https://brain.el80.space/mcp/", "headers": { "Authorization": "Bearer TOKEN" } } }
```

Los tools aparecen como `mcp__<server>__<tool>` en la lista de deferred tools al inicio de sesión.

### 9router MCP — stdio vs. HTTP remoto son mecanismos distintos

- **Plugins stdio:** `/api/mcp/[plugin]/sse` ejecuta `npx`/`python3` local. No proxia HTTP.
- **HTTP remoto:** `PATCH /api/settings {"mcpServers":[{name,url,transport:"http"}]}`.
- **Auth:** `POST /api/auth/login {"password":"..."}` → cookie `auth_token` (header `set-cookie`).

**Previene:** usar la ruta SSE de 9router para proxiar brain (solo funciona con stdio).

---

## Next.js — API Routes con fetch interno a Docker

Las rutas server-side (`app/api/*/route.ts`) corren dentro del contenedor `hermes-website` que está en la red `backend`. Acceden a otros servicios por hostname de Docker:

```typescript
const HERMES = process.env.HERMES_URL_INTERNAL ?? 'http://hermes:8080';
const LITELLM = process.env.LITELLM_URL_INTERNAL ?? 'http://litellm:4000';
```

### AbortSignal.timeout() — forma moderna de timeout en fetch

```typescript
const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
```

No usar `new AbortController()` + `setTimeout` + `clearTimeout` — `AbortSignal.timeout` es más limpio y disponible desde Node 17+.

### LiteLLM — Prometheus metrics y modelos caídos en silencio

Para exponer métricas a Prometheus: `callbacks: ["prometheus"]` en `litellm_settings`. El endpoint es `/metrics/` (trailing slash) — configurar `metrics_path: '/metrics/'` en prometheus.yml.

Si un modelo aparece en litellm.yaml pero no en `GET /v1/models`: LiteLLM lo deshabilitó silenciosamente tras fallo de API. Testear directo al proveedor para ver el error real — `RESOURCE_EXHAUSTED` = cuota agotada → redirigir por OpenRouter (`openrouter/<provider>/<model>`).

**Previene:** `litellm: down` en Prometheus y horas depurando config cuando el error es cuota/billing.

### LiteLLM 401 = servicio up

LiteLLM responde 401 cuando recibe una request sin autenticación válida, pero eso confirma que el servicio está corriendo. En health checks de la UI:

```typescript
litellmUp = [200, 401].includes(litellmRes.value.status);
```

---

## Harness Engineering — resumen de subsistemas

Artefactos: `CLAUDE.md`+`AGENTS.md` (instructions) · `PENDIENTES.json` (state) · `Makefile` (verification) · regla de scope · `SESSION_HANDOFF.md` (lifecycle).

### Makefile — SHELL := /bin/bash obligatorio

Cualquier Makefile que use `source`, arrays bash, o `[[ ]]` necesita esta línea al inicio:

```makefile
SHELL := /bin/bash
```

Sin esto, Make usa `/bin/sh` por defecto y `source /root/.env` falla silenciosamente — las variables de entorno no se cargan y los health checks fallan aunque el servicio esté running.

También: usar `set -a; source /root/.env 2>/dev/null; set +a` al inicio de cada recipe que necesite variables de entorno — exporta todas automáticamente.

**Previene:** health check que reporta DOWN por LITELLM_MASTER_KEY vacío.

### `docker compose ps` — output es "Up" no "running"

El comando `docker compose ps` muestra el estado como `Up X days (healthy)`, no como `running`. Cualquier grep sobre este output debe buscar `"Up"`:

```makefile
@if docker compose ps hermes 2>/dev/null | grep -q "Up"; then  # ✓
@if docker compose ps hermes 2>/dev/null | grep -q "running"; then  # ✗ no coincide
```

**Previene:** condición always-false que omite lint silenciosamente.

### `make doctor` — pipeline principal único

```bash
make doctor   # 6 pasos: repo → Docker → health → lint → harness → pendientes
```

Output: ✅ OK / ❌ problema / ⚠️ advertencia. Skill alternativo: `/pipeline` (explicaciones no-técnicas).

### Makefile — `|| true` en condiciones de archivo

Cualquier `[ -f ... ] && echo ...` al final de un recipe de Make debe terminar con `|| true`. Sin esto, si el archivo no existe, Make reporta error y aborta el target:

```makefile
# ❌ crashea si HANDOFF no existe:
[ -f "$$HANDOFF" ] && echo "pendiente"

# ✅ correcto:
[ -f "$$HANDOFF" ] && echo "pendiente" || true
```

**Previene:** `make: *** Error 1` al final de targets que verifican archivos opcionales.

### AGENTS.md — cuándo usarlo

`AGENTS.md` es el entry file de 100 líneas para el agente. CLAUDE.md es el detalle completo.
- Agente nuevo o context comprimido: leer `AGENTS.md` primero (startup, hard constraints, verification gate)
- Trabajo detallado: consultar CLAUDE.md para la sección relevante

### CLAUDE.md — presupuesto de tamaño (< 40 k chars)

El sistema lanza `Large CLAUDE.md will impact performance` cuando supera los 40 000 caracteres. Verificar en cada `/evolve`:

```bash
wc -c /root/CLAUDE.md   # debe ser < 40000
```

Si supera: comprimir prosa histórica ("Error en sesión...", "Aplicar desde...", "Por qué..." explicativos) — nunca eliminar reglas operativas. Target: < 39 500 para dejar margen.

### MEMORY.md — límite de 200 líneas

El índice de memoria (`memory/MEMORY.md`) tiene un cap efectivo de ~200 líneas. Entradas por encima del cap se truncan silenciosamente.

```bash
wc -l /root/.claude/projects/-root/memory/MEMORY.md   # verificar tamaño
```

Consolidar entradas redundantes cuando el índice supere 30 entradas. Los archivos de detalle (ej. `user_profile.md`) no tienen límite.

### Limpieza de /tmp entre sesiones

Al inicio de sesión, si hay archivos de agentes anteriores:

```bash
ls /tmp/claude_progress /tmp/*.md 2>/dev/null   # detectar leftovers
```

Si hay archivos de sesiones anteriores: revisar si contienen trabajo no integrado, luego limpiar.
El startup checklist ya incluye `rm -f /tmp/claude_progress`.

### Escalation de sub-agentes fallidos

- 1 fallo: reintentar con prompt más específico
- 2 fallos: intentar escritura directa por el orquestador
- 3 fallos o ambigüedad de scope: escalar al usuario — no continuar quemando tokens

---

## Infraestructura externa — referencias compactas

- **Hostinger DNS:** `https://developers.hostinger.com/api/dns/v1/zones/<dom>` (no `api.hostinger.com` → CF 530). PUT `overwrite:false` añade sin borrar.
- **SSL subdominio con wildcard `*→IP`:** HTTP-01/TLS-ALPN-01 fallan por caché ACME. Usar `~/.acme.sh/acme.sh --issue --dns dns_hostinger -d nuevo.el80.space --dnssleep 15` (key en `HOSTINGER_API_KEY`).
- **Digital Ocean:** cuentas nuevas solo `s-*` (max $56/mes). `doctl` no preinstalado — descargar de `github.com/digitalocean/doctl/releases`. Control Center: `104.236.74.0`, SSH key `/root/.ssh/do_droplet_key`, compose en `/root/control-center/`.
- **Tailscale:** `status` mostrando `active; offline` = sesión conocida pero nodo desconectado — verificar con `tailscale ping` antes de SSH. `tailscale up --advertise-tags=tag:infra --accept-routes` imprime URL de auth sin pre-generar key.
