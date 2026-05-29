# CLAUDE.md — Hermes Stack (router)

Instrucciones del proyecto para Claude Code. Se cargan automáticamente en cada sesión sobre `/root`.

Este archivo es un **router lean**: contiene solo las reglas universales (aplican a *toda* tarea) y una tabla que enruta a reglas de detalle por dominio. El detalle vive en `docs/rules/*.md` y se carga **bajo demanda** — así la capacidad de instrucciones es ilimitada sin chocar con el límite de 40k de CLAUDE.md.

---

## Router de instrucciones — OBLIGATORIO

Antes de escribir código o ejecutar comandos de un dominio, **leer con el tool `Read` el módulo correspondiente**. No actúes de memoria en estos dominios: las reglas contienen errores ya resueltos que no debes repetir.

| Si la tarea toca… | LEER primero |
|---|---|
| git push / commit / PR / branch / `.gitignore` / build pre-commit | `docs/rules/git.md` |
| sub-agentes / swarm / `/gg` / orquestación / paralelizar / versión de librería | `docs/rules/orchestration.md` |
| `website/` / Next.js / React / TypeScript / API routes / frontend | `docs/rules/nextjs.md` |
| LaTeX / `.tex` / XeLaTeX / generar PDF | `docs/rules/latex.md` |
| docker-compose / contenedores / healthcheck / servicios | `docs/rules/docker.md` |
| `hermes/` Python / aiohttp / orjson / performance del agente | `docs/rules/hermes-python.md` |
| brain / retrieval / embeddings / fastembed / RAG / MCP / 9router | `docs/rules/brain.md` |
| Makefile / `make doctor` / AGENTS.md / MEMORY.md / barra de progreso | `docs/rules/harness.md` |
| permisos / `settings.json` / `settings.local.json` | `docs/rules/permissions.md` |
| slash commands / `/evolve` / `/plan` / CI/CD / `deploy.yml` | `docs/rules/slash-commands.md` |
| DNS / SSL / Hostinger / Digital Ocean / Tailscale | `docs/rules/infra-externa.md` |
| deploy / health check / mapa de puertos / referencia del stack | `docs/rules/stack.md` |

Si una tarea cruza varios dominios, leer todos los módulos relevantes antes de empezar. Si dudas qué módulo aplica, escanea esta tabla por palabra clave.

**Al añadir reglas nuevas:** van al módulo `docs/rules/<dominio>.md`, no a este archivo. Solo reglas verdaderamente universales se añaden aquí.

---

## Reglas universales (aplican siempre)

### Estilo de comunicación — output mínimo

El usuario paga por cada token de output.

- **No narrar el procedimiento ni el progreso.** Nada de "voy a hacer X", "ahora hago Y", "completado Z". El diff y los commits cuentan la historia.
- **No mostrar el contenido completo de archivos editados** salvo petición explícita.
- **Chat:** silencioso durante el trabajo. Excepciones: bloqueo real → mensaje claro · cierre de turno → UNA línea con commit hash · petición explícita → explicar.

### Sesiones de voz — normalizar transcripción

Los prompts dictados por micrófono llegan con errores. Normalizar antes de procesar:

| Transcripción errónea | Correcta |
|---|---|
| `togen` | `tokens` |
| `pitline` | `pipeline` |
| `opus 4.7` / `opus 4.8` | el modelo más potente disponible |
| `swcion` / `sewion` / `ression` | `sesión` |
| `backgraund` / `bacgraun` | `background` |
| `orwuestador` / `orquertador` | `orquestador` |
| `jerarqia` / `gerarquia` | `jerarquía` |
| `metrivas` / `metriques` | `métricas` |
| `sintodo` / `sintax` | `sintaxis` |

Ante ambigüedad: inferir la interpretación más razonable en el contexto del stack antes de pedir aclaración.

### Planificación interna implícita

El usuario **no** necesita escribir `/plan`. Cualquier tarea no trivial (multi-paso, multi-archivo, multi-agente, con dependencias o riesgos) se planifica **internamente** (en thinking, no en output) antes de ejecutar:

1. Identificar archivos a tocar y el orden.
2. Detectar dependencias entre pasos.
3. Decidir si requiere swarm (ver `docs/rules/orchestration.md`) o escritura directa.
4. Verificar pre-condiciones (versión de librería, existencia de directorios, permisos).

Tareas triviales (un Edit puntual, un `git status`) → ejecutar sin plan. Solo entrar en plan mode formal si el usuario lo pide o el riesgo lo amerita (cambios irreversibles, refactors grandes, deploys).

### Edición de archivos

- **Leer el archivo completo antes de editar.** Nunca `Edit` al final sin haber leído las últimas líneas.
- Edición puntual → `Edit`. Más del 30% cambia → `Write` con archivo completo.
- **No appendear** secciones nuevas si ya existe una equivalente — editar la existente.
- **`Write` exige un `Read` previo del mismo archivo en esta sesión.** `Bash cat`/`head` NO cuentan → error "File has not been read yet".

### Git — esenciales (detalle en `docs/rules/git.md`)

- Push: incrustar token (`gh auth token`) en la URL HTTPS, push, restaurar URL limpia. Username `erikjosehrnndz-crypto`.
- `git add` siempre desde `/root` (o `git -C /root add`).
- Commit por tarea lógica, no por sesión. Commitear antes de lanzar orquestación multi-agente.

---

## Ciclo de sesión

### Inicio

```bash
git status                    # cambios sin commitear
git log --oneline -5          # commits recientes
docker compose ps             # estado del stack
rm -f /tmp/claude_progress    # limpiar barra de progreso stale
cat /root/SESSION_HANDOFF.md 2>/dev/null   # handoff anterior (si existe)
cat /root/PENDIENTES.md | head -20         # tareas activas
```

Si hay cambios sin commitear de una sesión anterior: analizarlos, commitearlos o descartarlos **antes** de empezar trabajo nuevo.

### Una tarea activa por sesión

Completar el ítem activo antes del siguiente. Tarea secundaria que surge → registrarla en PENDIENTES.md pero **no empezarla**. Excepciones: la activa bloquea por dependencia externa; o lanzar sub-agentes en paralelo dentro de una tarea.

### Definition of Done (los 4 criterios)

1. Implementación existe en código.
2. Verificación ejecutada — correr el comando real, no "debería funcionar".
3. Evidencia registrada — commit hash u output en PENDIENTES.md / SESSION_HANDOFF.md.
4. Stack reiniciable — `docker compose ps` muestra todos los servicios Up.

### Verificación gate — `make check`

```bash
make check        # build Next.js + health checks + lint Python
make health-check # solo health de servicios
make doctor       # pipeline completo (6 pasos)
```

Usar `make check` antes de declarar cualquier tarea completada.

### Cierre

1. Actualizar `estado`/`evidencia` del ítem en PENDIENTES.md.
2. `make health-check` — confirmar stack sano.
3. Commitear todo el trabajo — nunca dejar cambios sin commitear al cerrar.
4. Si hay trabajo incompleto: copiar `.claude/templates/session-handoff.md` → `/root/SESSION_HANDOFF.md` con el siguiente paso concreto.

---

## Perfil del usuario

Erik José Hernández, dueño del Hermes Stack, español. **Solo usa móvil** (sin desktop). No es programador — explicaciones operativas en español, sin jerga innecesaria. Prefiere docs en español.
