# CLAUDE.md — Hermes Stack

Instrucciones específicas del proyecto para Claude Code. Se aplican en todas las sesiones sobre este repositorio.

---

## Git

### Push HTTPS requiere token embedido
El remote usa HTTPS, no SSH. Para hacer push usar siempre:
```bash
GH_TOKEN=$(gh auth token)
git remote set-url origin "https://erikjosehrnndz-crypto:${GH_TOKEN}@github.com/erikjosehrnndz-crypto/hermes-stack.git"
git push
git remote set-url origin "https://github.com/erikjosehrnndz-crypto/hermes-stack.git"  # restaurar URL limpia
```

### Crear .gitignore antes de hacer git add en directorios nuevos
Antes de `git add` sobre cualquier directorio nuevo, verificar qué archivos contiene y crear `.gitignore` si hay artefactos de build, bases de datos o dependencias:
- `website/` → ignorar `node_modules/`, `dist/`
- `hermes_bp/` → ignorar `*.aux`, `*.toc`, `*.out`, `*.lot`, `*.log`, `*.synctex.gz`, `*.db`
- Cualquier directorio Python → ignorar `__pycache__/`, `*.pyc`, `.venv/`

### Nunca commitear estos archivos
- `*.db` (filebrowser.db, ruvector.db)
- `*.zip` (backups)
- `Sync/`, `snap/`
- Archivos de build LaTeX (`.aux`, `.toc`, `.out`, `.lot`, `.log`)
- `node_modules/`, `dist/` de frontend

### Commit al final de cada tarea lógica
No dejar cambios sin commit entre tareas. Si una sesión termina con cambios en el working tree, es un error de proceso.

---

## LaTeX / XeLaTeX

### Conflicto Babel español + TikZ
**Siempre** incluir `\usetikzlibrary{babel}` cuando se use `\usepackage[spanish]{babel}` con TikZ. Sin esto, `>=Stealth` en las flechas falla con error "I do not know the key '\par'".

```latex
\usepackage{tikz}
\usetikzlibrary{babel,arrows.meta,positioning,...}  % babel PRIMERO en la lista
```

### YAML en listings
El paquete `listings` no incluye YAML por defecto. Definirlo siempre en el preámbulo:
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

### Fuentes en XeLaTeX sin fontawesome
`fontawesome5` no está instalado en este VPS. Usar texto o símbolos Unicode directos en vez de `\faIcon{}`. Fuentes disponibles: DejaVu Serif, DejaVu Sans, DejaVu Sans Mono.

### Compilación correcta
XeLaTeX necesita 3 pasadas para TOC + hyperref + outlines:
```bash
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```
Verificar que no haya líneas `^!` en el `.log` antes de dar el PDF por bueno.

---

## Edición de archivos existentes (especialmente README)

**Siempre leer el archivo completo antes de editar.** Nunca usar `Edit` con `old_string` al final de un archivo sin haber leído las últimas líneas — puede haber contenido previo que invalida el contexto (secciones duplicadas, separadores rotos, enlaces locales).

Patrón correcto:
1. `Read` el archivo completo (o con `offset` si es muy largo)
2. Identificar qué secciones existen ya
3. Decidir si es edición puntual (`Edit`) o reescritura completa (`Write`)

---

## Sub-agentes vs escritura directa

**Usar sub-agentes** cuando el contenido a generar requiere investigación genuina o lectura de múltiples fuentes desconocidas.

**NO usar sub-agentes** cuando:
- El contenido fuente ya está en el contexto o en un archivo conocido (ej: `blueprint.txt`)
- La tarea es convertir/formatear contenido existente (ej: texto → LaTeX)
- La tarea cabe en < 30 min de escritura directa

**Riesgo de orquestación masiva:** Si se spawnean N agentes y todos chocan con rate limit, el trabajo se pierde completamente. Para tareas de escritura con contenido conocido, escribir directamente es más confiable que paralelizar.

---

## Stack de producción — datos clave

| Variable | Valor |
|---|---|
| Directorio VPS | `/root` |
| Dominio base | `el80.space` |
| Contenedores activos | 10 (ver `docker-compose.yml`) |
| Puerto Hermes | `127.0.0.1:8080` |
| Puerto LiteLLM | `127.0.0.1:4000` |
| Latencia E2E objetivo | < 500 ms |

Cambios al stack en producción: siempre health-check post-deploy antes de declarar éxito.
