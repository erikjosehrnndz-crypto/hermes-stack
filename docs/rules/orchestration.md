# Reglas — Sub-agentes y orquestación jerárquica

## Sub-agentes vs escritura directa

**Usar sub-agentes** cuando el contenido requiere investigación genuina en fuentes desconocidas o múltiples archivos que no están en contexto.

**Escribir directamente** cuando:
- El contenido fuente ya está en contexto o en un archivo conocido
- La tarea es convertir/reformatear algo existente (texto → LaTeX, etc.)
- La tarea es < 30 min de escritura directa

**Regla:** Si el contenido fuente ya existe → escribir directo. Solo paralelizar si la investigación genuinamente lo requiere y cada agente escribe su output a disco antes de terminar.

## Checkpointing obligatorio en sub-agentes

Cada sub-agente que produzca contenido debe escribirlo a un archivo en disco (ej. `/tmp/<task_id>.md`) como **última acción antes de terminar** — no solo retornarlo en la respuesta. Previene pérdida del 100% del trabajo si el orquestador choca con rate limit antes de recolectar.

## Sub-agentes no heredan permisos Write/Bash del padre

El orquestador debe configurar `.claude/settings.json` antes de lanzarlos, o escribir él mismo los archivos con los resultados.

## CLAUDE.md y docs/rules/ solo los edita el agente principal

Los sub-agentes que editan archivos de instrucciones reciben un security warning ("self-modification soft block"). Patrón: sub-agentes investigan y devuelven hallazgos como texto; el agente principal hace el `Edit`/`Write` final.

## Síntesis incremental y contexto en sub-agentes

Con 4+ agentes en paralelo, lanzar síntesis de forma incremental (excepción: si necesita TODOS los inputs, esperar es correcto). Incrustar contexto necesario (MEMORY.md, reglas relevantes) en los prompts — el orquestador no debe hacer Bash/Read sobre trabajo ya delegado.

## Economía de modelos

- **Haiku:** lectura de archivos, extracción de datos, mapeo estructural
- **Sonnet:** síntesis, redacción técnica, generación de documentos
- **Opus:** orquestador raíz SIEMPRE, o sub-agente si el usuario lo activa explícitamente

## El orquestador raíz SIEMPRE usa el mejor modelo disponible

Cualquier `/gg`, `/swarm`, plan multi-agente o tarea con sub-agentes **debe** ser orquestado por el modelo más potente disponible (actualmente **Opus 4.8**, `claude-opus-4-8`).

1. Si el modelo activo no es el más potente del momento, avisar al usuario y sugerir `/model` antes de proceder.
2. El orquestador raíz **nunca** se degrada a Sonnet/Haiku — los modelos pequeños son SOLO para sub-agentes.

## Sub-agentes pueden lanzar sub-swarms — solo con autorización del padre

Un sub-agente que necesite paralelizar debe **retornar primero** su solicitud (razón, agentes propuestos, tokens estimados, outputs a `/tmp/`) — nunca lanzar directamente. Profundidad máxima: 3 niveles. Toda autorización fluye top-down. Previene explosión de costes.

## Sub-agentes de larga duración → `run_in_background: true`

Cualquier sub-agente cuya tarea estimada exceda **60 segundos**. El orquestador recibe notificación automática al completar, no debe `sleep` ni hacer polling.

**Regla práctica:** lectura simple → foreground · investigación/redacción → background · síntesis final → foreground.

## Plan jerárquico explícito al inicio del swarm

Antes de lanzar agentes, documentar la jerarquía: cada agente lleva rol, modelo (Haiku/Sonnet/Opus), modo (background/foreground) y dependencias de output.

## Escalation de sub-agentes fallidos

- 1 fallo: reintentar con prompt más específico
- 2 fallos: intentar escritura directa por el orquestador
- 3 fallos o ambigüedad de scope: escalar al usuario — no continuar quemando tokens

## Dependencias — verificar versión antes de usar features

```bash
cat node_modules/<lib>/package.json | grep '"version"' | head -1
npm list <lib>
```

El check de versión debe ser el **primer paso** cuando el plan menciona archivos de configuración version-específicos. Verificar primero, escribir después.
