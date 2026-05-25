# /paxupdate — Auto-mejora proactiva del harness

**Propósito:** auditar el estado *actual* de los 5 subsistemas del harness y aplicar correcciones concretas sobre los artefactos reales. A diferencia de `/gg` (retrospectivo sobre transcripts), `/paxupdate` actúa sobre el estado presente del repositorio.

---

## Pre-condiciones

1. Ejecutar el checklist de inicio de sesión (git status, docker compose ps, rm -f /tmp/claude_progress) si no se ha hecho.
2. El modelo activo debe ser el más potente disponible si se anticipa reescritura mayor de CLAUDE.md. Para audits rápidos, el modelo actual es suficiente.
3. Hacer commit de cualquier trabajo en curso **antes** de iniciar — `/paxupdate` puede editar PENDIENTES.md, Makefile, AGENTS.md, CLAUDE.md y SESSION_HANDOFF.md.

---

## Fase 1 — AUDIT (directo, sin sub-agentes)

Leer los artefactos y ejecutar los checks. El orquestador lo hace directamente porque los archivos son conocidos y pequeños. Solo escalar a sub-agentes si CLAUDE.md requiere análisis profundo de contenido (ver Fase 3).

### 1.1 Instructions

```bash
wc -l /root/AGENTS.md /root/CLAUDE.md 2>/dev/null
```

Checks:
- AGENTS.md ≤ 100 líneas (si supera: candidato a trim)
- CLAUDE.md contiene "Definition of Done" y "clock-out" (grep para confirmar)
- No hay secciones duplicadas en CLAUDE.md (verificar visualmente si > 1000 líneas)

Resultado → `instructions_status` + lista de defectos

### 1.2 State

```bash
cat /root/PENDIENTES.md | grep -E "^- \[|state:|evidence:|fecha:" | head -40
ls /root/PENDIENTES.json 2>/dev/null && echo "JSON presente" || echo "JSON ausente"
```

Checks:
- Todos los ítems tienen campo `state:` definido
- Todos los ítems con state `done` tienen campo `evidence:` con valor (no vacío)
- Ningún ítem lleva > 7 días con `state: active` sin actualización
- PENDIENTES.json existe y está sincronizado con el MD

Resultado → `state_status` + lista de ítems defectuosos con su ID (hs-XXX)

### 1.3 Verification

```bash
make -n check 2>&1 | head -20
grep -n '"running"' /root/Makefile 2>/dev/null || echo "OK: no hay 'running'"
grep -n '"Up"' /root/Makefile 2>/dev/null | head -5
cat /root/PENDIENTES.md | grep -E "verification:" | head -10
```

Checks:
- `make check` es un target válido y ejecutable
- El Makefile no usa grep `"running"` (debe ser `"Up"`)
- Cada ítem de PENDIENTES con state `active` tiene campo `verification:` explícito
- El Makefile tiene `SHELL := /bin/bash` como primera línea

Resultado → `verification_status` + lista de defectos con línea de archivo

### 1.4 Scope

```bash
grep -c "state: active" /root/PENDIENTES.md 2>/dev/null || echo "0"
grep "state: active" /root/PENDIENTES.md 2>/dev/null
```

Checks:
- ≤ 1 ítem en `state: active`
- Si hay > 1 activo: listar todos para resolución

Resultado → `scope_status` + lista de activos en exceso

### 1.5 Session Lifecycle

```bash
ls -la /root/SESSION_HANDOFF.md 2>/dev/null && echo "handoff EXISTS" || echo "handoff ABSENT"
grep -n "siguiente paso" /root/SESSION_HANDOFF.md 2>/dev/null | head -3
grep -n "rm -f /tmp/claude_progress" /root/CLAUDE.md | head -2
```

Checks:
- Si SESSION_HANDOFF.md existe: tiene "siguiente paso recomendado" con valor no vacío
- CLAUDE.md tiene `rm -f /tmp/claude_progress` en el checklist de inicio
- No hay archivos /tmp/pax_*.md o /tmp/gg_*.md de sesiones anteriores sin integrar

Resultado → `session_status` + defectos encontrados

---

## Fase 2 — SÍNTESIS

Generar el action plan priorizado:

```
/paxupdate — YYYY-MM-DD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Instructions   [✅/⚠️/❌]  <detalle en una línea>
State          [✅/⚠️/❌]  <detalle en una línea>
Verification   [✅/⚠️/❌]  <detalle en una línea>
Scope          [✅/⚠️/❌]  <detalle en una línea>
Session        [✅/⚠️/❌]  <detalle en una línea>
```

Severidad:
- `❌ crítico` — rompe Definition of Done o bloquea make check → corregir en esta ejecución
- `⚠️ advertencia` — deuda técnica que crece entre sesiones → corregir si no requiere decisión del usuario
- `💡 sugerencia` — mejora de calidad sin impacto inmediato → registrar pero no aplicar solo

Si todos los subsistemas están en ✅: reportar "Harness en buen estado — sin acciones requeridas" y detener.

---

## Fase 3 — APPLY

El orquestador aplica los cambios directamente. Orden de prioridad: ❌ primero, luego ⚠️.

### Instructions — cuándo actuar
- AGENTS.md > 100 líneas: trim de la sección más verbosa sin eliminar hard constraints
- CLAUDE.md con sección duplicada: merge de la duplicada en la existente
- Regla contradictoria o stale: editar la existente (nunca appendear)
- **Si se requiere reescritura mayor de CLAUDE.md (> 30% del contenido):** escalar a swarm con patrón de `/gg`

### State — cuándo actuar
- Ítem sin campo `state:` → añadir `state: pending` como default
- Ítem `done` sin `evidence:` → añadir `evidence: (pendiente de verificación)`
- Ítem `active` > 7 días sin update → añadir nota `stale:` con fecha actual y mover a `state: pending`
- **No cerrar ítems como done** sin evidencia real — eso lo decide el usuario

### Verification — cuándo actuar
- Makefile con grep `"running"` → corregir a `"Up"` (es un bug silencioso)
- Makefile sin `SHELL := /bin/bash` → añadir como primera línea
- Ítem PENDIENTES `active` sin campo `verification:` → añadir `verification: (definir comando)`
- Target `make check` roto: reportar el error exacto al usuario — no arreglar ciegamente

### Scope — cuándo actuar
- > 1 ítem `state: active`: mover todos menos el más reciente a `state: pending`
- Añadir nota `paused-by: /paxupdate` para que el usuario sepa qué se pausó

### Session — cuándo actuar
- SESSION_HANDOFF.md existe con "siguiente paso" vacío: añadir `"Ver PENDIENTES.md ítem activo"` como default
- Archivos /tmp/pax_*.md o /tmp/gg_*.md sin integrar: listarlos al usuario, no borrarlos sin permiso

**Regla general de apply:** si la corrección requiere una decisión del usuario (ej. qué ítem de los 2 activos tiene prioridad), reportarlo sin aplicar y esperar instrucción.

---

## Fase 4 — VERIFY + COMMIT

```bash
# Verificación gate
make check

# Solo si make check pasa:
git add /root/PENDIENTES.md /root/Makefile /root/AGENTS.md /root/CLAUDE.md /root/SESSION_HANDOFF.md 2>/dev/null
git status  # revisar qué cambió realmente
git commit -m "chore: /paxupdate $(date +%Y-%m-%d) — N mejoras en harness [subsistemas]"
```

Si `make check` falla: reportar el error al usuario **sin hacer commit**. El estado del harness post-apply es el que queda en disco — el usuario puede revertir con `git checkout`.

---

## Reporte final al usuario

```
ACCIONES APLICADAS (N):
1. [Verification] Makefile:45 — corregido grep "running" → "Up"
2. [State] PENDIENTES.md:hs-002 — añadido stale: 2026-05-25, movido a pending
3. [Scope] PENDIENTES.md — pausado hs-004 (exceso de activos)

make check: ✅ / ❌ <error>
Commit: <hash> / sin commit (make check falló)
```

Si no hubo acciones: una línea. Si hubo > 5 acciones: lista completa.

---

## Escalación a swarm

Solo si la Fase 3 detecta que CLAUDE.md requiere reescritura mayor (> 30% del contenido cambia):

1. Reportar al usuario qué secciones necesitan reescritura y por qué.
2. Solicitar autorización explícita para lanzar swarm.
3. Si autorizado: seguir el patrón de swarm de `/gg` (Researcher + Memory Specialist + orquestador síntesis).
4. Los sub-agentes escriben a `/tmp/pax_<rol>.md` antes de terminar (checkpointing obligatorio).
5. El orquestador (nunca los sub-agentes) escribe CLAUDE.md final.

---

## Principios

- **Proactivo, no retrospectivo:** actúa sobre el estado actual, no sobre lo que pasó.
- **Mínima fricción:** solo hacer cambios que corrigen defectos observados — no mejoras cosméticas.
- **Transparente:** si una acción requiere decisión del usuario, reportar y esperar — no adivinar.
- **Idempotente:** ejecutar `/paxupdate` dos veces seguidas debe producir el mismo resultado (ya en ✅ → sin cambios → sin commit).
