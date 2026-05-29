# Reglas — Slash commands, /plan, /evolve, CI/CD

## Slash commands globales (`~/.claude/commands/`)

- `~/.claude/commands/` no existe por defecto — `mkdir -p` antes del primer slash command global.
- `/evolve` es **prospectivo**: reglas añadidas al cerrar sesión benefician la siguiente, no rescatan la actual.
- Transcripts multi-sesión en `/root/.claude/projects/-root/<sessionId>.jsonl`, índice en `/root/.claude/history.jsonl`.

## /plan con Ruflo disponible → proponer swarm desde el inicio

Si la tarea involucra investigación multi-dominio + síntesis, proponer swarm (Researcher / Memory Specialist / Reviewer / Coder) — no enfoque secuencial con bash.

## /plan con "SOTA" / "máximo esfuerzo" → WebSearch ANTES de diseñar

Trigger: "state of the art", "lo mejor", "máxima calidad", "máximo esfuerzo". Lanzar ≥2 Explore agents con WebSearch antes de diseñar — el conocimiento de entrenamiento tiene cutoff fijo y las librerías líderes cambian (GraphRAG → LightRAG, etc.). Previene diseño obsoleto que requiere re-trabajo completo.

## CI/CD pipeline — referencia

GitHub Actions → SSH al VPS → `git pull /root` → `docker compose up -d --build` → health checks autenticados → **rollback automático a `HEAD~1` si el health check falla**.

Leer `.github/workflows/deploy.yml` antes de:
- Hacer push a `main`
- Modificar el workflow de deploy
- Cambiar health check endpoints

## Recursos de referencia del proyecto

- **Blueprint:** `/root/Hermes_Stack_Blueprint.pdf` (52 pp) — arquitectura completa. Leer antes de tareas de contexto profundo.
