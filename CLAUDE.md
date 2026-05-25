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
```

Si hay cambios sin commitear de una sesión anterior: analizarlos, commitearlos o descartarlos **antes** de empezar trabajo nuevo.

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
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push -u origin feat/mi-feature
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
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

---

## Sub-agentes vs escritura directa

**Usar sub-agentes** cuando el contenido requiere investigación genuina en fuentes desconocidas o múltiples archivos que no están en contexto.

**Escribir directamente** cuando:
- El contenido fuente ya está en contexto o en un archivo conocido
- La tarea es convertir/reformatear algo existente (texto → LaTeX, etc.)
- La tarea es < 30 min de escritura directa

**Riesgo crítico de orquestación masiva:** Si N agentes chocan con rate limit simultáneamente, el trabajo se pierde al 100% si no hay archivos escritos en disco. En sesión 2026-05-24, 5 agentes LaTeX cayeron por rate limit y `hermes_bp/` quedó vacío. Rehacerlo directo tomó 20 min.

**Regla:** Si el contenido fuente ya existe → escribir directo. Solo paralelizar si la investigación genuinamente lo requiere y cada agente escribe su output a disco antes de terminar.

### Checkpointing obligatorio en sub-agentes

Cada sub-agente que produzca contenido debe escribirlo a un archivo en disco (ej. `/tmp/<task_id>.md`) como **última acción antes de terminar** — no solo retornarlo en la respuesta del agente.
Previene: pérdida del 100% del trabajo cuando el orquestador choca con rate limit antes de recolectar resultados.

### Sub-agentes no heredan permisos Write/Bash del padre

Los sub-agentes lanzados con TaskCreate no heredan permisos Write/Bash del orquestador. Si un agente necesita escribir archivos o ejecutar comandos, el orquestador debe configurar `.claude/settings.json` antes de lanzarlo, o el orquestador debe escribir él mismo los archivos con los resultados.
Previene: ciclo de bloqueos de permisos que consume rate limit sin producir archivos.

### Síntesis incremental con 4+ agentes en paralelo

Con 4 o más agentes en paralelo, lanzar el agente de síntesis de forma **incremental** a medida que cada investigador completa — no esperar todos los resultados simultáneamente.
Previene: bloqueo total si el orquestador sufre rate limit esperando al último agente.

### El orquestador no debe investigar trabajo que delegó

Si el usuario delega explícitamente y prohíbe al orquestador hacer Bash/Read, el orquestador debe incrustar el contexto necesario (desde MEMORY.md, CLAUDE.md) en los prompts de los sub-agentes, no leer archivos directamente.
Previene: consumo de tokens del orquestador en trabajo que fue delegado.

### Economía de modelos en orquestación multi-agente

Asignar el modelo mínimo suficiente por fase:
- **Haiku:** lectura de archivos, extracción de datos, mapeo estructural
- **Sonnet:** síntesis, redacción técnica, generación de documentos
- **Opus:** solo si el usuario lo activa explícitamente

En sesión 2026-05-23, 4 agentes Haiku produjeron ~3400 líneas estructuradas. Usar Sonnet/Opus hubiera costado 3-5x más para el mismo resultado.

---

## Dependencias — verificar versión antes de usar features

Antes de usar una característica específica de versión de cualquier librería, verificar la versión instalada:

```bash
cat node_modules/<lib>/package.json | grep '"version"' | head -1
# o bien:
npm list <lib>
```

**No asumir que la versión instalada soporta las últimas features.** Error cometido en 2026-05-25: se usó `next.config.ts` (feature de Next.js 15+) pero la versión instalada era 14.2.x, que no lo soporta — build roto hasta renombrar a `.mjs`.

**Regla de orden:** el check de versión debe ser el **primer paso** cuando el plan menciona archivos de configuración version-específicos (ej. `next.config.ts`, plugins con breaking changes). Verificar primero, escribir después.
Previene: el ciclo write→build-error→fix que ya ocurrió.

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

```latex
\lstdefinelanguage{yaml}{
  keywords={true,false,null,yes,no},
  keywordstyle=\color{hermesblue}\bfseries,
  sensitive=false,
  comment=[l]{\#},
  morestring=[b]',
  morestring=[b]",
}
```

### Fuentes disponibles en este VPS

```
DejaVu Serif / DejaVu Sans / DejaVu Sans Mono  ✓
fontawesome5                                    ✗  (no instalado)
```

No usar `\faIcon{}`. Sustituir con texto o Unicode directo.

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

### El directorio no existe en instalaciones limpias

`~/.claude/commands/` debe crearse manualmente antes de escribir el primer slash command global:

```bash
mkdir -p ~/.claude/commands/
```

No existe por defecto — escribir un archivo en esa ruta sin crear el directorio primero falla silenciosamente o con error de path.

### /gg es efectivo para la PRÓXIMA sesión, no la actual

Las reglas añadidas con `/gg` al final de una sesión no previenen errores que ya ocurrieron en esa misma sesión — benefician la sesión siguiente. El valor de `/gg` es **prospectivo**.

---

## CI/CD pipeline — referencia

GitHub Actions → SSH al VPS → `git pull /root` → `docker compose up -d --build` → health checks autenticados → **rollback automático a `HEAD~1` si el health check falla**.

Leer `.github/workflows/deploy.yml` antes de:
- Hacer push a `main`
- Modificar el workflow de deploy
- Cambiar health check endpoints

---

## Recursos de referencia del proyecto

### Blueprint PDF

`/root/Hermes_Stack_Blueprint.pdf` (52 páginas) es el documento técnico de referencia del stack completo: arquitectura, diagramas, todos los servicios. Leer antes de tareas que requieran contexto profundo del stack.

### Estructura LaTeX base validada

`main.tex + s1_architecture.tex + s2_services.tex + s3_cicd.tex + s4_observability.tex` compila limpia (24 pp, 0 errores XeLaTeX). Usar como punto de partida para futuros documentos técnicos del proyecto.

---

## Docker — nombres de servicio vs contenedor

En este proyecto hay una distinción importante para `docker compose up --no-deps`:

| Servicio (`docker compose`) | Contenedor (`docker inspect`) |
|---|---|
| `litellm` | `litellm-router` |
| `hermes` | `hermes-agent` |
| `whisper-stt` | `whisper-stt` |

El watchdog y cualquier script que use `docker compose up --no-deps <servicio>` debe usar el **nombre de servicio**, no el nombre de contenedor.

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

## Sesiones de voz / remote-control

Los prompts dictados por micrófono llegan con errores de transcripción. Normalizar antes de procesar:

| Transcripción errónea | Interpretación correcta |
|---|---|
| `togen` | `tokens` |
| `pitline` | `pipeline` |
| `opus 4.7` | el modelo más potente disponible en ese momento |

Ante ambigüedad en un prompt de voz, inferir la interpretación más razonable en el contexto del stack antes de pedir aclaración.
