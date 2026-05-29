---
name: 2026-05-25_karpathy_pattern
type: source
source_type: conversation
source_date: 2026-05-25
source_url: "https://karpathy.github.io/2014/05/15/memory/"
ingested_date: 2026-05-25
ingested_by: wiki_synthesizer_agent
---

# Fuente: Patron Karpathy aplicado a esta wiki

El "patron Karpathy" es una metodologia de mantenimiento de bases de conocimiento personal donde un LLM actua como sistema de ingest continuo: lee nuevas fuentes, extrae hechos atomicos, y actualiza las paginas existentes sin crear duplicados. El resultado es una wiki viva que refleja el estado actual del conocimiento del propietario.

## Resumen

Este documento describe como se aplico el patron Karpathy al diseno de la wiki del Hermes Stack, las decisiones de estructuracion y los principios que guian el mantenimiento continuo.

## Principios del patron Karpathy

1. **Hechos atomicos:** cada unidad de conocimiento es una afirmacion independiente y verificable. No parrafos narrativos.

2. **Sin duplicados:** antes de crear una pagina nueva, buscar si ya existe con nombre similar. Si existe, editar la existente.

3. **Trazabilidad:** cada hecho puede remontarse a su origen. Las paginas `sources/` son el registro de procedencia.

4. **Ingest incremental:** el LLM procesa una fuente nueva a la vez, distribuye los hechos a las paginas correctas, y actualiza los cross-links bidireccionales.

5. **Mantenimiento periodico (lint):** el sistema detecta referencias rotas, paginas huerfanas y datos obsoletos.

6. **Fuentes inmutables:** las paginas `sources/` no se editan despues de crearse. Si el documento original cambia, se crea una nueva fuente con fecha mas reciente.

## Como se aplico a la wiki Hermes

### Estructura elegida

Se definieron cuatro tipos de paginas alineados con las necesidades del stack:

- **entities/:** servicios Docker activos — capturan el "que" (configuracion actual, runbooks, health checks)
- **concepts/:** patrones arquitectonicos — capturan el "por que" (razonamiento detras de decisiones)
- **topics/:** guias operativas — capturan el "como" (procedimientos paso a paso)
- **sources/:** fuentes ingestadas — capturan el "de donde" (trazabilidad)

### Decisiones de diseno especificas

- **Frontmatter YAML:** compatible con Obsidian, VitePress, Hugo. Parseable automaticamente por agentes.
- **Links `[[nombre]]`:** sintaxis Obsidian para navegabilidad en editores compatibles.
- **Naming snake_case:** consistente, sin ambiguedad, compatible con grep/find.
- **`_index.md` y `_schema.md`:** prefijados con `_` para distinguirlos de paginas de contenido.
- **Git-backed:** el historial de commits refleja la evolucion del conocimiento. `git log wiki/` revela cuando cambio cada pagina.

### Leccion de la primera ingest

La primera ingest (2026-05-25) ingesto CLAUDE.md y los archivos de memoria como fuentes. Los hechos se distribuyeron a:
- 10 paginas de entities/ (servicios del stack)
- 7 paginas de concepts/ (patrones y decisiones)
- 5 paginas de topics/ (guias operativas)

El schema se diseno antes de crear paginas para garantizar consistencia entre agentes en un swarm.

## Hechos clave extraidos

- El LLM como sistema de ingest es mas eficiente que ingest manual para bases de conocimiento tecnico
- La bidireccionalidad de links es critica para encontrar paginas huerfanas
- La distincion entities/concepts/topics evita mezclar "que es" con "como se usa"
- Las fuentes inmutables garantizan auditabilidad de cambios en el conocimiento

## Referencias cruzadas

- [[wiki_maintenance]] — implementacion del lint periodico del patron
- [[ingest_new_source]] — procedimiento de ingest paso a paso
- [[agent_orchestration]] — como paralelizar ingestas largas con multiples agentes
- [[_schema]] — el schema de la wiki que implementa este patron
