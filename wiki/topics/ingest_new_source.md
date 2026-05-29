---
name: "Ingest New Source"
type: "topic"
difficulty: "intermediate"
time_estimate: "15-45 min"
involves: ["agent_orchestration", "wiki_maintenance"]
last_updated: "2026-05-25"
---

# Ingest New Source

En una línea: cómo añadir una nueva fuente de conocimiento a esta wiki siguiendo el patrón Karpathy — extraer hechos atómicos de un documento y distribuirlos a las páginas correctas sin crear duplicados.

## Por qué importa

La wiki es útil solo si se mantiene sincronizada con la realidad del stack. Cuando llega un nuevo ADR, un issue importante, un log de deploy significativo o una conversación técnica relevante, hay que ingerirlos de forma estructurada para que el conocimiento sea buscable y trazable.

## Pasos

### 1. Crear la página fuente (inmutable)

Crear `wiki/sources/YYYY-MM-DD_<descripcion>.md`:

```markdown
---
name: "Título descriptivo del documento"
type: "source"
source_type: "blueprint|adr|issue|log|conversation|ticket"
source_date: "YYYY-MM-DD"
source_url: "https://... o file:///ruta/local"
ingested_date: "YYYY-MM-DD"
ingested_by: "nombre_agente_o_persona"
---

## Resumen
[1 párrafo de qué trata el documento]

## Hechos clave extraídos
- Hecho atómico 1
- Hecho atómico 2
- ...

## Citas relevantes
> "texto literal del documento"
> — página X, sección Y

## Referencias cruzadas
- [[entidad_mencionada]]
- [[concepto_relacionado]]
```

Esta página **no se edita** después de crearse. Si el documento cambia, crear una nueva fuente con fecha más reciente.

### 2. Mapear hechos a entidades existentes

Para cada hecho extraído que mencione una entidad (`entities/`):
- Abrir la página de la entidad.
- Leer completo antes de editar — puede haber secciones de sesiones anteriores.
- Actualizar solo las secciones relevantes: configuración, dependencias, runbook.
- Añadir link a la fuente: `[[2026-05-25_nueva_fuente]]`.
- Actualizar `last_reviewed: YYYY-MM-DD`.

### 3. Mapear hechos a conceptos existentes

Para cada hecho que introduce o refina un patrón/decisión:
- Buscar si ya existe un concepto relacionado en `wiki/concepts/`.
- Si existe: editar la sección relevante (no appendear al final sin leer).
- Si no existe: crear `wiki/concepts/<nombre>.md` siguiendo el schema de [[wiki_maintenance]].

### 4. Actualizar guías operativas (topics/) si aplica

Si el documento modifica un procedimiento operativo:
- Buscar el topic relevante en `wiki/topics/`.
- Actualizar los pasos afectados.
- Añadir el gotcha o nota nueva si el documento revela un error conocido.

### 5. Actualizar `_index.md`

Añadir la nueva fuente a la sección de fuentes del índice:

```markdown
- [[2026-05-25_nueva_fuente]] — resumen breve de qué aporta
```

Si se crearon páginas nuevas (entidades o conceptos), añadirlas a las tablas correspondientes del índice.

### 6. Verificar enlaces bidireccionales

Si `entities/A.md` enlaza a `entities/B.md`, verificar que `entities/B.md` también enlace a A.

```bash
# Buscar referencias a una página
grep -r "[[nombre_pagina]]" /root/wiki/
```

### 7. Commitear la ingest

```bash
git add wiki/sources/YYYY-MM-DD_<desc>.md
git add wiki/entities/<entidades_actualizadas>.md
git add wiki/concepts/<conceptos_actualizados>.md
git add wiki/topics/<topics_actualizados>.md
git add wiki/_index.md
git commit -m "wiki: ingest YYYY-MM-DD — descripción breve de la fuente"
```

## Notas

- **No duplicar páginas:** antes de crear una entidad o concepto nuevo, buscar si ya existe con nombre similar.
- **Hechos atómicos:** cada hecho en la fuente debe ser una afirmación independiente y verificable, no un párrafo narrativo.
- **Fuentes inmutables:** si el documento original cambia (ej. nueva versión del Blueprint), crear `sources/YYYY-MM-DD_v2_<desc>.md` — no editar la fuente original.
- **Sub-agentes para ingestas largas:** si el documento tiene >50 páginas (como el Blueprint de 52 pp), usar [[agent_orchestration]] con agentes Haiku para extracción paralela por sección. Cada agente hace checkpoint en `/tmp/<section>.md`.

## Gotchas

- Appendear al final de una página sin leerla puede crear contenido duplicado o contradictorio con secciones anteriores.
- Las fuentes externas (URLs) pueden caer — incluir siempre una cita o resumen local en la página fuente.
- Si se usa orquestación multi-agente para la ingest: commitear el trabajo previo antes de lanzar los agentes, y verificar checkpoints en `/tmp/` antes de que el orquestador recolecte resultados.

## Véase también

- [[wiki_maintenance]] — lint periódico para mantener la wiki sana
- [[agent_orchestration]] — cómo paralelizar ingestas largas
- `wiki/sources/` — ejemplos de fuentes ya ingestadas
