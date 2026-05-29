---
name: "Agent Orchestration"
type: "concept"
category: "pattern"
status: "active"
introduced_date: "2026-05-01"
last_reviewed: "2026-05-25"
---

# Agent Orchestration

El patrón de orquestación multi-agente distribuye tareas de desarrollo entre agentes especializados (Researcher, Coder, Memory Specialist, Reviewer) coordinados por un agente orquestador. El objetivo es paralelizar trabajo independiente reduciendo tiempo total, con salvaguardas ante rate limit y pérdida de estado.

## Por qué existe

Tareas complejas de desarrollo (investigación multi-fuente, síntesis de documentación, generación de código + tests simultáneos) son más rápidas cuando se dividen entre agentes especializados en paralelo. Sin embargo, la orquestación ingenua tiene riesgos críticos: rate limit simultáneo en múltiples agentes puede resultar en pérdida total del trabajo si los outputs no están checkpointados en disco.

## Cómo funciona

### Roles de agentes

| Rol | Modelo recomendado | Tarea |
|---|---|---|
| Researcher | Haiku | Lectura de archivos, extracción de datos, mapeo estructural |
| Coder | Sonnet | Escritura de código, tests, implementación |
| Memory Specialist | Haiku | Búsqueda en memoria, comparación con estado anterior |
| Reviewer | Sonnet | Validación de outputs, síntesis final |
| Orquestador | Sonnet | Coordina todo, escribe CLAUDE.md, hace commits |

### Economía de modelos

- **Haiku:** investigación y extracción (fase barata). Validado: 4 agentes Haiku produjeron ~3400 líneas estructuradas a ~286k tokens.
- **Sonnet:** síntesis, redacción técnica, generación de documentos.
- **Opus:** solo cuando el usuario lo activa explícitamente (`/model Opus`).

Usar Sonnet/Opus para investigación cuesta 3-5x más sin mejora en la calidad de extracción.

### Checkpointing obligatorio

Cada sub-agente que produzca contenido debe escribirlo a disco antes de terminar:

```bash
# Cada agente escribe su output aquí
/tmp/<task_id>.md
```

Nunca retornar solo en la respuesta del agente: si el orquestador choca con rate limit antes de recolectar resultados, el trabajo se pierde al 100%.

### Reglas críticas de orquestación

1. **Commit antes de lanzar agentes:** todo trabajo no commiteado antes de lanzar sub-agentes puede perderse si el context limit ocurre durante la ejecución paralela.
2. **Sub-agentes no heredan permisos:** los agentes lanzados con TaskCreate no heredan permisos Write/Bash del orquestador. Configurar `.claude/settings.json` previamente o hacer que el orquestador escriba los archivos.
3. **CLAUDE.md solo lo edita el agente principal:** los sub-agentes que intentan editar CLAUDE.md reciben un security warning. El patrón correcto es que devuelvan hallazgos como texto y el orquestador sintetice.
4. **Síntesis incremental:** con 4+ agentes, lanzar el sintetizador a medida que cada investigador completa — no esperar a todos simultáneamente. Excepción: si el sintetizador necesita todos los inputs para coherencia.
5. **El orquestador no investiga lo que delegó:** incrustar el contexto necesario (desde CLAUDE.md, MEMORY.md) en los prompts de los sub-agentes.

### Cuándo NO usar sub-agentes

- El contenido fuente ya está disponible en contexto.
- La tarea es convertir/reformatear algo existente.
- La tarea tarda menos de 30 min de escritura directa.

El riesgo crítico de orquestación masiva: en sesión 2026-05-24, 5 agentes LaTeX cayeron por rate limit y `hermes_bp/` quedó vacío. Rehacerlo directo tomó 20 min.

## Entidades relacionadas

- [[github_actions]] — pipeline de CI/CD, también un tipo de orquestación
- [[hermes_agent]] — agente conversacional del stack (diferente al concepto de agent aquí)

## Trade-offs

- **Ganado:** paralelización real de trabajo independiente, especialización por rol, economia de modelos.
- **Perdido:** complejidad de coordinación, riesgo de pérdida por rate limit si no hay checkpointing, overhead de configuración de permisos por sub-agente.

## Evolución

- El patrón de checkpointing a `/tmp/` surgió de la sesión 2026-05-24 donde se perdió trabajo.
- La restricción de permisos de sub-agentes se descubrió experimentalmente.
- La regla de síntesis incremental surgió del riesgo de bloqueo total al esperar al último agente.

## Referencias

- [[ingest_new_source]] — ejemplo de workflow donde la orquestación aplica
- [[wiki_maintenance]] — workflow de mantenimiento que puede paralelizarse
