# Reglas — Harness Engineering

Artefactos: `CLAUDE.md` (router) + `docs/rules/*.md` (detalle) + `AGENTS.md` (entry) — instructions · `PENDIENTES.json` (state) · `Makefile` (verification) · `SESSION_HANDOFF.md` (lifecycle).

## Makefile — `SHELL := /bin/bash` obligatorio

Cualquier Makefile que use `source`, arrays bash o `[[ ]]` necesita al inicio:

```makefile
SHELL := /bin/bash
```

Sin esto Make usa `/bin/sh` y `source /root/.env` falla silenciosamente. Usar `set -a; source /root/.env 2>/dev/null; set +a` al inicio de cada recipe que necesite env vars.

## `docker compose ps` — output es "Up" no "running"

```makefile
@if docker compose ps hermes 2>/dev/null | grep -q "Up"; then  # ✓
```

Grep por `"running"` es always-false.

## Makefile — `|| true` en condiciones de archivo

```makefile
[ -f "$$HANDOFF" ] && echo "pendiente" || true
```

Sin `|| true`, si el archivo no existe Make aborta con `Error 1`.

## `make doctor` — pipeline principal único

```bash
make doctor   # 6 pasos: repo → Docker → health → lint → harness → pendientes
```

Output: ✅ OK / ❌ problema / ⚠️ advertencia. Skill alternativo: `/pipeline` (explicaciones no-técnicas).

## AGENTS.md — cuándo usarlo

Entry file de 100 líneas. Agente nuevo o context comprimido: leer `AGENTS.md` primero (startup, hard constraints, verification gate). Trabajo detallado: consultar el módulo `docs/rules/` relevante.

## CLAUDE.md — presupuesto de tamaño (< 40 k chars)

El sistema lanza `Large CLAUDE.md will impact performance` sobre 40 000 caracteres. `CLAUDE.md` ahora es un router lean — el detalle vive en `docs/rules/*.md` (sin límite individual práctico). Verificar en cada `/evolve`:

```bash
wc -c /root/CLAUDE.md   # debe ser < 40000 (router típicamente << 10k)
```

Reglas nuevas de un dominio van al módulo `docs/rules/<dominio>.md`, no a `CLAUDE.md`. Solo reglas verdaderamente universales van al router.

## MEMORY.md — límite de 200 líneas

```bash
wc -l /root/.claude/projects/-root/memory/MEMORY.md
```

Entradas sobre el cap se truncan silenciosamente. Consolidar cuando el índice supere 30 entradas. Los archivos de detalle no tienen límite.

## Barra de progreso

Vive en `statusLine` via hook `PostToolUse` + `statusline.sh` (NO en chat). Iniciar: `echo "0|<N_pasos>|<task>|0|$(date +%s)" > /tmp/claude_progress`. Auto-incrementa, auto-limpia al 100%. Implementación: sin `set -euo pipefail`, string slicing no `seq`, detectar sub-agentes solo si hay archivo de progreso activo.

## Limpieza de /tmp entre sesiones

```bash
ls /tmp/claude_progress /tmp/*.md 2>/dev/null   # detectar leftovers
```

Revisar si contienen trabajo no integrado, luego limpiar. El startup checklist incluye `rm -f /tmp/claude_progress`.
