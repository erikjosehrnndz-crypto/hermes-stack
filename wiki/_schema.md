---
name: _schema
type: meta
last_updated: 2026-05-25
---

# Wiki Schema — Hermes Stack

## Filosofia

La wiki Hermes es una base de conocimiento incremental mantenida por agentes y actualizaciones manuales. Sigue el patron Karpathy: el LLM ingesta nuevas fuentes, extrae hechos atomicos y actualiza las paginas existentes sin crear duplicados. Es la fuente unica de verdad operativa del stack, complementaria al Blueprint y CLAUDE.md.

## Estructura de directorios

```
wiki/
├── _index.md          # Indice maestro — linkea todas las paginas
├── _schema.md         # Este archivo — guia de ingest y lint
├── entities/          # Servicios, herramientas, maquinas, personas, APIs
├── concepts/          # Patrones arquitectonicos, workflows, decisiones
├── topics/            # Guias operativas transversales (como hacer X)
└── sources/           # Resumenes de documentos ingestados (inmutables)
```

## Tipos de paginas

### entities/
Entidades concretas: servicios Docker activos, herramientas, dominios, personas.
- Naming: `snake_case.md` (ej: `litellm_router.md`)
- Contenido: descripcion, configuracion, dependencias, health check, runbook, metricas

### concepts/
Patrones abstractos y decisiones de diseno que cruzan multiples entidades.
- Naming: `snake_case.md` (ej: `voice_pipeline_e2e.md`)
- Contenido: definicion, por que existe, como funciona, trade-offs, evolucion

### topics/
Guias operativas narrativas enfocadas en un objetivo (como hacer X).
- Naming: `snake_case.md` (ej: `deployment_workflow.md`)
- Contenido: pasos numerados, gotchas, entidades implicadas, vease tambien

### sources/
Resumenes de documentos ingestados. **Inmutables** despues de crearse.
- Naming: `YYYY-MM-DD_<descripcion>.md` (ej: `2026-05-25_claude_md.md`)
- Contenido: resumen, hechos clave extraidos, citas, referencias cruzadas

## Frontmatter obligatorio por tipo

**entities/**
```yaml
---
name: Nombre de la Entidad
type: service|tool|machine|person|api|domain
status: active|deprecated|planning|archived
port: 4000
domain: subdomain.el80.space
port_name: nombre_servicio_compose
docker_network: backend|monitoring
health_check_endpoint: GET /health
last_updated: YYYY-MM-DD
---
```

**concepts/**
```yaml
---
name: "Nombre del Concepto"
type: concept
category: architecture|workflow|pattern|principle|problem-solution
status: active|evolving|deprecated
introduced_date: YYYY-MM-DD
last_reviewed: YYYY-MM-DD
---
```

**topics/**
```yaml
---
name: "Nombre del Topic"
type: topic
difficulty: beginner|intermediate|advanced
time_estimate: "5-10 min"
involves: [entidad_a, concepto_b]
last_updated: YYYY-MM-DD
---
```

**sources/**
```yaml
---
name: "Titulo del Documento"
type: source
source_type: blueprint|adr|issue|log|conversation|ticket
source_date: YYYY-MM-DD
source_url: "https://... o file:///ruta/local"
ingested_date: YYYY-MM-DD
ingested_by: nombre_agente_o_persona
---
```

## Reglas de ingest (anadir nueva fuente)

1. Crear `sources/YYYY-MM-DD_<desc>.md` con resumen y hechos atomicos extraidos.
2. Para cada hecho que mencione una entidad: abrir `entities/<nombre>.md`, leer completo, actualizar solo secciones relevantes. Actualizar `last_updated`.
3. Para cada hecho que refine un patron o decision: buscar `concepts/` existente. Si existe, editar. Si no, crear.
4. Si aplica a un procedimiento operativo: actualizar el `topics/` correspondiente.
5. Actualizar `_index.md`: anadir nuevas paginas a las secciones correspondientes.
6. Verificar enlaces bidireccionales: si A menciona B, confirmar que B menciona A.
7. Commit: `git commit -m "wiki: ingest YYYY-MM-DD — descripcion breve"`

## Reglas de lint (mantenimiento periodico)

1. **Paginas huerfanas:** buscar paginas sin ningun link entrante. Linkar desde `_index.md` o pagina relacionada.
2. **Referencias rotas:** `grep -roh "\[\[[^]]*\]\]" /root/wiki/` — verificar que cada `[[nombre]]` tiene un archivo correspondiente.
3. **Contradicciones:** si dos paginas dicen cosas distintas sobre el mismo hecho, resolver contra la fuente de verdad (`docker-compose.yml`, `package.json`, etc.).
4. **Staleness:** paginas con `last_reviewed` > 3 meses merecen revision.
5. **Runbooks obsoletos:** verificar comandos contra `docker-compose.yml` y `deploy.yml` actuales.
6. **No editar sources:** si hay un error en una fuente, corregirlo en la pagina que la usa, no en la fuente.

## Convenciones de cross-links

- Sintaxis: `[[nombre_pagina]]` sin extension `.md`.
- `entities → entities`: dependencias directas (A requiere B → A enlaza B).
- `entities → concepts`: patrones que la entidad implementa.
- `concepts → entities`: entidades que implementan el concepto.
- `topics → entities + concepts`: cada paso enlaza entidades/conceptos implicados.
- `sources → entities + concepts`: trazabilidad de hechos extraidos.
- `_index.md`: unica pagina que lista todas las demas.
- Bidireccionalidad: si A enlaza B, B debe enlazar A.
