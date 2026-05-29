---
name: 2026-05-25_memory_files
type: source
source_type: conversation
source_date: 2026-05-25
source_url: "file:///root/.claude/projects/-root/memory/"
ingested_date: 2026-05-25
ingested_by: wiki_synthesizer_agent
---

# Fuente: Archivos de memoria del agente

Los archivos de memoria en `/root/.claude/projects/-root/memory/` son la memoria persistente del agente Claude Code entre sesiones. Contienen el perfil del usuario, estado actual del proyecto, y feedback acumulado de sesiones anteriores.

## Resumen

El directorio de memoria incluye: perfil del usuario (Erik Jose Hernandez), estado del proyecto Hermes Stack, y multiples archivos de feedback sobre patrones aprendidos de errores en sesiones anteriores. Estos archivos complementan CLAUDE.md con contexto personal y lecciones especificas de sesion.

## Hechos clave extraidos

### Perfil del usuario
- **Nombre:** Erik Jose Hernandez
- **Email:** erikjosehernandez@gmail.com
- **Idioma preferido:** Espanol (docs y comunicacion)
- **Rol:** Owner y operador del Hermes Stack
- **Dominio:** el80.space

### Estado del proyecto
- Plataforma IA autohospedada en VPS unico
- Dominio: el80.space
- Repositorio: github.com/erikjosehrnndz-crypto/hermes-stack
- 10 contenedores Docker activos
- Latencia E2E objetivo: < 500 ms
- Fecha de referencia: 2026-05-25

### Feedback sobre orquestacion
- Usar sub-agentes SOLO si el contenido requiere investigacion genuina
- Si el contenido fuente ya esta disponible, escribir directo es mas rapido y seguro
- Sesion 2026-05-24: 5 agentes LaTeX cayeron por rate limit → hermes_bp/ quedo vacio; rehacerlo directo tomo 20 min

### Feedback sobre economia de tokens
- Haiku: investigacion y extraccion (fase barata)
- Sonnet: sintesis y redaccion tecnica
- Opus: solo cuando el usuario lo activa explicitamente
- 4 agentes Haiku produjeron ~3400 lineas a ~286k tokens (validado en sesion 2026-05-23)

### Feedback sobre Git
- Push HTTPS con token incrustado en URL es el unico metodo que funciona
- .gitignore antes de `git add` en cualquier directorio nuevo
- Commit por tarea logica, no al final de la sesion

### Feedback sobre edicion de archivos
- Leer el archivo completo antes de editar
- No appendear secciones nuevas si ya existe una equivalente

### Referencia Google Drive
- Carpeta "proyecto os" tiene ID documentado en la memoria
- Portafolio de documentos del proyecto

## Citas relevantes

> "Usar sub-agentes SOLO si el contenido requiere investigacion genuina en fuentes desconocidas o multiples archivos que no estan en contexto."
> — feedback_orchestration.md

> "Haiku para investigacion, Sonnet para sintesis, Opus solo cuando el usuario lo pide."
> — feedback_token_economy.md

## Referencias cruzadas

- [[agent_orchestration]] — feedback de orquestacion consolidado en concepto
- [[https_git_push]] — feedback de practicas Git
- [[deployment_workflow]] — feedback de practicas Git aplicado al workflow
- [[hermes_agent]] — estado del proyecto: 10 contenedores activos
- [[voice_pipeline_e2e]] — objetivo SLO <500ms documentado
