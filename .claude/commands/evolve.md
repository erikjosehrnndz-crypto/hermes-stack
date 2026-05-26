# /evolve — Evolución integral del harness

**Propósito:** en una sola ejecución, hacer dos cosas complementarias:
1. **Proactivo:** auditar el estado actual de los 5 subsistemas del harness y aplicar correcciones sobre los artefactos reales.
2. **Retrospectivo:** extraer aprendizajes de la sesión actual y actualizar `CLAUDE.md` con reglas nuevas o corregidas.

Reemplaza: `/gg`, `/harness-creator`, `/paxupdate`

---

## Pre-condiciones

1. Hacer commit de cualquier trabajo en curso — `/evolve` puede editar CLAUDE.md, AGENTS.md, PENDIENTES.md, Makefile y SESSION_HANDOFF.md.
2. **Modelo activo debe ser el más potente disponible** si se anticipa reescritura mayor de CLAUDE.md (> 30% del contenido). Para el caso típico, el modelo activo es suficiente.
3. El checklist de inicio de sesión debe haberse ejecutado (`rm -f /tmp/claude_progress`, docker compose ps, etc.).

---

## Fase 1 — AUDIT PROACTIVO

Leer los artefactos y ejecutar los 5 checks directamente (sin sub-agentes — los archivos son conocidos y pequeños).

### 1.1 Instructions

```bash
wc -l /root/AGENTS.md /root/CLAUDE.md 2>/dev/null
grep -c "Definition of Done" /root/CLAUDE.md
grep -c "clock-out\|Protocolo de cierre" /root/CLAUDE.md
```

Checks:
- AGENTS.md ≤ 100 líneas
- CLAUDE.md contiene "Definition of Done" y sección de clock-out
- No hay secciones duplicadas (verificar si > 1000 líneas)

### 1.2 State

```bash
# PENDIENTES.json es la fuente canónica (campos: status, evidence, verification)
jq -r '.[] | "\(.id)  status=\(.status)  evidence=\(.evidence)"' /root/PENDIENTES.json 2>/dev/null
ls /root/PENDIENTES.json 2>/dev/null && echo "JSON presente" || echo "JSON ausente"
```

Checks:
- Todos los ítems tienen campo `status` definido (not-started / active / done)
- Ítems `done` tienen `evidence` con valor no vacío
- Ningún ítem `active` lleva > 7 días sin actualización (verificar fecha de update en git log)
- PENDIENTES.json sincronizado con el MD (misma lista de IDs)

### 1.3 Verification

```bash
make -n check 2>&1 | head -20
grep -n '"running"' /root/Makefile 2>/dev/null || echo "OK: no 'running'"
head -3 /root/Makefile
# Ítems activos sin verification en JSON:
jq -r '.[] | select(.status == "active") | select(.verification == "") | .id' /root/PENDIENTES.json 2>/dev/null
```

Checks:
- `make check` es un target válido y ejecutable
- Makefile no usa grep `"running"` (debe ser `"Up"`)
- Makefile tiene `SHELL := /bin/bash` como primera línea
- Cada ítem `active` de PENDIENTES.json tiene campo `verification` no vacío

### 1.4 Scope

```bash
jq -r '[.[] | select(.status == "active")] | length' /root/PENDIENTES.json 2>/dev/null || echo "0"
jq -r '.[] | select(.status == "active") | .id' /root/PENDIENTES.json 2>/dev/null
```

Checks:
- ≤ 1 ítem en `status: active`

### 1.5 Session Lifecycle

```bash
ls -la /root/SESSION_HANDOFF.md 2>/dev/null && echo "EXISTS" || echo "ABSENT"
grep -n "siguiente paso" /root/SESSION_HANDOFF.md 2>/dev/null | head -3
grep -c "rm -f /tmp/claude_progress" /root/CLAUDE.md
```

Checks:
- Si SESSION_HANDOFF.md existe: tiene "siguiente paso recomendado" con valor no vacío
- CLAUDE.md tiene `rm -f /tmp/claude_progress` en el checklist de inicio

**Scoring por subsistema:** ✅ OK / ⚠️ advertencia / ❌ crítico

---

## Fase 2 — RETROSPECTIVA DE SESIÓN

Revisar el historial de la conversación actual buscando:

- **Correcciones del usuario:** "no", "stop", "eso no es", "vuelve a hacer X" → regla a añadir
- **Confirmaciones no obvias:** "perfecto, así", "sigue así", elección aceptada sin pushback → validación a registrar
- **Ciclos write → error → fix:** especialmente versionado de librerías, paths inexistentes, permisos de sub-agentes
- **Pérdidas de trabajo:** rate limit, context limit, checkpointing ausente
- **Prompts de voz corruptos:** transcripciones erróneas nuevas no mapeadas en CLAUDE.md

Si no se detecta ninguna fricción en la sesión actual: la Fase 2 produce resultado vacío y se omite en el apply.

Cada hallazgo → candidato a regla con:
- Patrón obligatorio (qué hacer)
- **Previene:** error específico + referencia sesión/fecha
- **Cómo aplicar:** cuándo activar

---

## Fase 3 — SÍNTESIS

Consolidar hallazgos de Fase 1 (audit) y Fase 2 (retrospectiva). Reporte previo al apply:

```
/evolve — YYYY-MM-DD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUDIT PROACTIVO
  Instructions   [✅/⚠️/❌]  <detalle en una línea>
  State          [✅/⚠️/❌]  <detalle en una línea>
  Verification   [✅/⚠️/❌]  <detalle en una línea>
  Scope          [✅/⚠️/❌]  <detalle en una línea>
  Session        [✅/⚠️/❌]  <detalle en una línea>

RETROSPECTIVA
  Reglas nuevas:      N  (listadas a continuación)
  Reglas a corregir:  N
  Sin hallazgos:      [sí/no]
```

Prioridad de apply: `❌ audit` > `correcciones retrospectiva` > `⚠️ audit` > `sugerencias retrospectiva`

Si todos los subsistemas están en ✅ y la retrospectiva no tiene hallazgos: reportar "Harness en buen estado — sin acciones" y detener.

Severidad:
- `❌ crítico` — rompe Definition of Done o bloquea make check → corregir siempre
- `⚠️ advertencia` — deuda técnica creciente → corregir si no requiere decisión del usuario
- `💡 sugerencia` — mejora de calidad → registrar, no aplicar solo

---

## Fase 4 — APPLY

El orquestador escribe directamente. Nunca los sub-agentes (aplica la regla de CLAUDE.md sobre auto-modificación).

### Harness artifacts (del audit)

**Instructions:**
- AGENTS.md > 100 líneas → trim de la sección más verbosa sin eliminar hard constraints
- CLAUDE.md con sección duplicada → merge en la existente; nunca appendear

**State:**
- Ítem sin `status` en JSON → añadir `"status": "not-started"` como default
- Ítem `done` con `evidence` vacío en JSON → añadir `"evidence": "(pendiente de verificación)"`
- Ítem `active` > 7 días → añadir nota en MD, mover a `"status": "not-started"` en JSON
- **No cerrar ítems como done** sin evidencia real

**Verification:**
- Makefile con grep `"running"` → corregir a `"Up"` (bug silencioso)
- Makefile sin `SHELL := /bin/bash` → añadir como primera línea
- Ítem `active` con `verification` vacío en JSON → añadir `"verification": "(definir comando)"`

**Scope:**
- > 1 ítem `status: active` → mover todos menos el más reciente a `status: not-started`, añadir nota en PENDIENTES.md con `paused-by: /evolve`

**Session:**
- SESSION_HANDOFF.md con "siguiente paso" vacío → añadir `"Ver PENDIENTES.md ítem activo"`

### CLAUDE.md (de la retrospectiva)

- Añadir reglas nuevas en la sección correspondiente (no crear sección nueva si ya existe una equivalente)
- Corregir reglas previas ambiguas o contraproducentes — editar la existente, no duplicar
- Si surge nueva preferencia del usuario → actualizar `~/.claude/projects/-root/memory/<tipo>_<slug>.md` y registrar en MEMORY.md

**Regla de apply:** si una corrección requiere decisión del usuario (ej. qué ítem de los 2 activos tiene prioridad, o si una regla contradice otra existente), reportar y esperar instrucción — no adivinar.

**Escalación a swarm:** solo si CLAUDE.md necesita reescritura > 30% del contenido:
1. Reportar al usuario qué secciones necesitan reescritura y por qué.
2. Solicitar autorización explícita para lanzar swarm.
3. Si autorizado: 1 agente Researcher (Haiku, background) + 1 Memory Specialist (Haiku, background). Cada uno escribe a `/tmp/evolve_<rol>.md` antes de terminar (checkpointing obligatorio). El orquestador (nunca los sub-agentes) escribe CLAUDE.md final.

---

## Fase 5 — VERIFY + COMMIT

```bash
make check

# Solo si make check pasa:
git add /root/CLAUDE.md /root/PENDIENTES.md /root/Makefile /root/AGENTS.md /root/SESSION_HANDOFF.md 2>/dev/null
git status  # revisar qué cambió realmente antes de commitear
git commit -m "chore: /evolve $(date +%Y-%m-%d) — N mejoras harness + M reglas CLAUDE.md"
```

Si `make check` falla: reportar el error exacto al usuario sin hacer commit.

---

## Reporte final

```
ACCIONES APLICADAS (N):
  Audit:         [lista de correcciones en artefactos]
  Retrospectiva: [lista de reglas añadidas/corregidas en CLAUDE.md]

make check: ✅ / ❌ <error>
Commit: <hash> / sin commit (make check falló)
```

Si no hubo acciones: una línea. Sin listas vacías.

---

## Principios

- **Doble cobertura:** corrige el harness *ahora* (audit proactivo) y previene errores futuros (retrospectiva).
- **Mínima fricción:** solo aplica cambios que corrigen defectos observados — sin mejoras cosméticas.
- **Transparente:** si una acción requiere decisión del usuario, reportar y esperar.
- **Idempotente:** ejecutar `/evolve` dos veces seguidas produce el mismo resultado (en ✅ → sin cambios → sin commit).
- **`/evolve` es prospectivo:** las reglas escritas en CLAUDE.md benefician sesiones futuras, no intentan rescatar la sesión en curso.
