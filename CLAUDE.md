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

### Push HTTPS — requiere token embedido en cada sesión

El remote usa HTTPS, no SSH. `git push` falla con "could not read Username". Patrón obligatorio:

```bash
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"
```

Restaurar la URL limpia después de cada push — el token no debe quedar en el remote URL.

### .gitignore antes de `git add` en cualquier directorio nuevo

Antes de hacer `git add <dir>/`, hacer `ls -la <dir>` e identificar artefactos. Reglas específicas de este proyecto:

| Directorio | Ignorar |
|---|---|
| `hermes_bp/` | `*.aux *.toc *.out *.lot *.log *.synctex.gz *.db` |
| `website/` | `node_modules/ dist/` |
| cualquier Python | `__pycache__/ *.pyc .venv/` |

El `.gitignore` raíz tiene `.*` que ignora todos los dotfiles. Para que los `.gitignore` de subdirectorios funcionen, el raíz debe tener `!.gitignore` como excepción — ya está añadido.

### Archivos que nunca van al repositorio

```
*.db              # filebrowser.db, ruvector.db — bases de datos runtime
*.zip             # backups y archivos de exportación
Sync/  snap/      # directorios del sistema
*.aux *.toc *.out *.lot *.log   # artefactos LaTeX
node_modules/  dist/            # dependencias y builds de frontend
.env  .env.*                    # secretos
```

### Commit por tarea lógica, no por sesión

Commitear al finalizar cada tarea individual. No acumular cambios de múltiples tareas en un solo commit al final de la sesión — si la sesión cae por rate limit, el trabajo sin commit se pierde.

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
