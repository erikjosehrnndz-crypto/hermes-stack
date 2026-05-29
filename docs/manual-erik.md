# Manual de Uso — Claude Code · Hermes Stack
> Tu referencia rápida. Diseñado para escanear, no para leer de arriba a abajo.

---

## ⚡ PANEL DE CONTROL — Respuesta en < 5 segundos

| Si estás aquí... | Haz esto | Por qué |
|---|---|---|
| Inicio de sesión | `make doctor` | Estado completo del stack en 1 comando |
| "¿Qué tengo pendiente?" | `cat /root/PENDIENTES.md \| head -30` | Tu backlog ordenado por prioridad |
| "El stack no responde" | `/pipeline` | Diagnóstico en lenguaje simple + guía |
| "Quiero cambiar código" | Pídelo directamente en el chat | Claude lo hace — no necesitas comandos |
| "¿Funcionó el cambio?" | `make check` | Build + health + lint en 1 comando |
| "Quiero hacer un commit" | Pídele a Claude que haga el commit | Usa el patrón HTTPS correcto automáticamente |
| "Sesión larga, quiero parar" | Pide "haz clock-out" | Claude actualiza PENDIENTES, commit, handoff |
| "Nueva sesión, ¿dónde estaba?" | `cat /root/SESSION_HANDOFF.md` | El paso siguiente está escrito literalmente |
| "Quiero que Claude recuerde algo" | "recuerda que..." en el chat | Lo guarda en su memoria permanente |
| "El harness está desactualizado" | `/evolve` | Audita y actualiza CLAUDE.md automáticamente |

---

## 🔄 FLUJO DE SESIÓN

```
┌─────────────────────────────────────────────────────────────────┐
│  CLOCK-IN (cada sesión nueva)                                   │
│                                                                 │
│  make doctor          → ver estado real del stack               │
│  cat PENDIENTES.md    → ver qué hay activo / pendiente          │
│  cat SESSION_HANDOFF.md  → ver si hay trabajo a continuar       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  ELEGIR TAREA (UNA sola a la vez)                               │
│                                                                 │
│  🔴 Prioridad alta primero (hs-001, hs-002...)                  │
│  Si surge otra tarea → pedirle a Claude que la registre         │
│  pero NO empezarla ahora                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  EJECUTAR (chat con Claude)                                     │
│                                                                 │
│  Describir qué quieres → Claude investiga + implementa          │
│  Si es algo urgente / riesgoso → Claude te pide confirmación    │
│  Si usas voz → dictar directamente, Claude normaliza errores    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  VERIFICAR (Definition of Done — los 4 criterios)               │
│                                                                 │
│  ✅ 1. Código implementado                                      │
│  ✅ 2. make check → sin errores                                 │
│  ✅ 3. Evidencia en PENDIENTES.md (commit hash o output real)   │
│  ✅ 4. docker compose ps → todos los servicios Up               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CLOCK-OUT                                                      │
│                                                                 │
│  Pide: "haz clock-out"                                          │
│  Claude hace: PENDIENTES.md → commit → SESSION_HANDOFF.md       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 SLASH COMMANDS

| Comando | Cuándo usarlo | Qué hace |
|---|---|---|
| `/evolve` | Al final de sesiones largas o cuando algo falló y no estaba documentado | Audita los 5 subsistemas del harness, extrae aprendizajes, actualiza CLAUDE.md |
| `/pipeline` | Cuando el stack falla y no sabes por dónde empezar | Ejecuta `make doctor` y te explica en lenguaje simple qué está mal |

> **Tip ADHD:** Estos comandos son los de mantenimiento, no los de trabajo diario. El chat normal cubre el 95% de lo que necesitas.

---

## 🔧 SKILLS RUFLO — Cuándo activarlos

Escribe la frase clave en el chat y Claude usa el skill automáticamente.

### Diagnóstico y estado del sistema
| Frase que dices | Skill que activa | Recibes |
|---|---|---|
| "estado del stack" / "qué está corriendo" | `ruflo-core:ruflo-status` | Salud de servicios + MCP + agentes |
| "diagnóstico completo" | `ruflo-core:ruflo-doctor` | Análisis profundo del harness |
| "audita la seguridad" | `ruflo-security-audit:audit` | Vulnerabilidades y dependencias |

### Memoria y contexto
| Frase que dices | Skill que activa | Recibes |
|---|---|---|
| "busca en tu memoria..." / "recuerdas cuando..." | `ruflo-rag-memory:recall` | Resultados semánticos de sesiones anteriores |
| "guarda esto en memoria" / "recuerda que..." | `ruflo-rag-memory:ruflo-memory` | Almacenado permanentemente |

### Código y documentación
| Frase que dices | Skill que activa | Recibes |
|---|---|---|
| "genera tests para [archivo]" | `ruflo-testgen:testgen` | Tests con análisis de cobertura |
| "documenta [módulo/función]" | `ruflo-docs:ruflo-docs` | Documentación generada |
| "revisa este PR" / "revisa el diff" | `code-review` | Bugs y problemas de calidad |

### Automatización y background
| Frase que dices | Skill que activa | Recibes |
|---|---|---|
| "programa X cada [intervalo]" | `ruflo-loop-workers:ruflo-loop` | Worker recurrente en background |
| "activa autopilot para..." | `ruflo-autopilot:autopilot` | Agente autónomo ejecutando en background |

### Rastreo de costos
| Frase que dices | Skill que activa | Recibes |
|---|---|---|
| "cuánto costó esta sesión" | `ruflo-cost-tracker:ruflo-cost` | Desglose en USD por agente |
| "optimiza mi uso de tokens" | `ruflo-cost-tracker:cost-optimize` | Recomendaciones específicas |

---

## 🌳 ÁRBOL DE DECISIÓN

```
¿Qué necesitas ahora?
│
├─► El stack no responde / algo está caído
│   └─► /pipeline  →  si no basta: make logs → docker compose ps
│
├─► Quiero cambiar código / añadir funcionalidad
│   ├─► Describir qué quieres en el chat (Claude implementa)
│   └─► Después: make check → si pasa → pedir commit
│
├─► No sé qué hay pendiente
│   └─► cat /root/PENDIENTES.md | head -30
│       └─► Si necesitas más detalle: cat /root/PENDIENTES.json
│
├─► Quiero que Claude recuerde algo para siempre
│   └─► "recuerda que [X]" en el chat
│       └─► Claude lo guarda en ~/.claude/projects/-root/memory/
│
├─► Hay un error misterioso que no entiendo
│   ├─► make logs  → últimas líneas de cada servicio
│   ├─► docker compose ps → ver qué servicios están Up/Down
│   └─► Pegar el error en el chat → Claude lo diagnostica
│
├─► Quiero saber cuánto estoy gastando en tokens/IA
│   └─► "cuánto costó esta sesión" en el chat
│
├─► Terminé la sesión y quiero cerrar bien
│   └─► "haz clock-out" en el chat
│
└─► El harness / CLAUDE.md está desactualizado o incompleto
    └─► /evolve  (mejor al final de una sesión larga)
```

---

## 🧠 TIPS ADHD+AACC

### 1. Voz → acción sin fricción
```bash
# En el prompt de Claude, el prefijo ! ejecuta comandos directamente:
! make doctor
! cat /root/PENDIENTES.md
! docker compose ps
```
Dicta el comando y el output aparece en la conversación. No necesitas abrir otra terminal.

### 2. Una tarea activa — el sistema te protege del rabbit hole
Cuando surge una idea secundaria mientras trabajas:
- Di "anota esto para después: [idea]"
- Claude la registra en PENDIENTES.md
- Tú sigues con lo que estabas haciendo
- PENDIENTES.md es tu buffer externo de memoria

### 3. Recuperar contexto entre sesiones en 30 segundos
```bash
cat /root/SESSION_HANDOFF.md
```
El archivo tiene literalmente "el siguiente paso es: [instrucción concreta]".  
No necesitas reconstruir contexto — ya está escrito.

### 4. Señales de que Claude entiende vs adivina
| Claude entiende | Claude adivina |
|---|---|
| Cita archivos específicos con rutas | Habla en genérico ("deberías...") |
| Ejecuta comandos y muestra output real | Dice "probablemente funciona" |
| Propone verificación concreta | No propone forma de verificar |
| Pide confirmación antes de cambios irreversibles | Actúa sin preguntar en cambios de riesgo |

Si ves señales de "adivina" → pide: "¿leíste el archivo? muéstrame qué encontraste exactamente"

### 5. Opus vs Sonnet — cuándo importa
| Situación | Modelo | Por qué |
|---|---|---|
| Trabajo diario, cambios de código, preguntas | Sonnet (default) | Suficientemente capaz, mucho más barato |
| Orquestación multi-agente compleja | Opus 4.7 | Mejor descomposición de tareas grandes |
| Documentos importantes, arquitectura crítica | Opus 4.7 | Calidad de razonamiento notablemente mayor |

Para cambiar: escribe `/model` en el chat.

### 6. Cuando Claude se "atasca" o da vueltas
Si después de 2 intentos el resultado no está bien:
1. Escribe: "Para. Dime exactamente qué estás intentando hacer y qué encontraste."
2. Claude reporta su estado — así identificas si el problema es de comprensión o de ejecución.
3. Si sigue atascado después de 3 intentos → escala: "hazlo tú directamente" (escritura directa) o "usa un sub-agente".

### 7. El chat es tu terminal principal
No necesitas abrir terminales separadas. Puedes:
- Pedir que ejecute comandos
- Ver los outputs directamente en el chat
- Pedir que interprete los outputs
- Pedir que tome acción basada en lo que vio

---

## 🌐 SERVICIOS Y PUERTOS — Referencia rápida

| Servicio | URL pública | Puerto local | Estado esperado |
|---|---|---|---|
| Hermes Agent | hermes.el80.space | 127.0.0.1:8080 | `Up` + `/health` 200 |
| LiteLLM Router | litellm.el80.space | 127.0.0.1:4000 | `Up` + `/health` 200 |
| Website | docs.el80.space | 127.0.0.1:3001 | `Up` |
| Grafana | grafana.el80.space | 127.0.0.1:3000 | `Up` |
| FileBrowser | files.el80.space | 127.0.0.1:8095 | `Up` |
| Whisper STT | — (interno) | 127.0.0.1:9000 | `Up` |
| Prometheus | — (interno) | 127.0.0.1:9090 | `Up` |

```bash
# Verificar todo de una vez:
make health-check

# Ver estado rápido:
make status
```

---

## 📋 COMANDOS MAKE — Cheat Sheet

```bash
make doctor        # Diagnóstico completo (6 pasos: git + docker + health + lint + harness + pendientes)
make check         # Verificación rápida: build Next.js + health + lint Python
make health-check  # Solo health de Hermes y LiteLLM
make build-check   # Solo build Next.js
make lint-check    # Solo lint Python (ruff + black)
make status        # docker compose ps
make logs          # Últimas 40 líneas de hermes + litellm + website
make clean-tmp     # Limpiar archivos temporales (/tmp/claude_progress, /tmp/*.md)
```

---

## 📚 GLOSARIO MÍNIMO

| Término | Qué es en la práctica |
|---|---|
| **harness** | El conjunto de archivos que hacen que Claude trabaje bien en tu proyecto: CLAUDE.md + AGENTS.md + PENDIENTES.json + Makefile + hooks |
| **skill** | Una capacidad especializada de Claude que se activa con frases clave (ej: "genera tests"). No necesitas saber el nombre técnico — solo describe lo que quieres |
| **swarm** | Varios agentes de Claude trabajando en paralelo en subtareas de un problema grande. Claude lo orquesta automáticamente cuando la tarea lo amerita |
| **sub-agente** | Un agente que Claude lanza internamente para hacer parte del trabajo (investigar, escribir un archivo, analizar código). Tú no los controlas directamente |
| **PENDIENTES.json** | Tu backlog estructurado — cada tarea tiene: id, prioridad, estado, comando de verificación, evidencia. Claude lo actualiza; tú lo consultas |
| **SESSION_HANDOFF.md** | Nota de Claude a Claude: "esto es exactamente lo que quedó pendiente y el siguiente paso concreto". Permite retomar en 30 segundos |
| **Definition of Done** | Los 4 criterios que una tarea debe cumplir para considerarse terminada (implementación + verificación + evidencia + stack Up) |
| **clock-in / clock-out** | El checklist de inicio y cierre de sesión. Garantiza que cada sesión empieza con estado conocido y termina con trabajo guardado |
| **MCP** | Protocolo que permite a Claude usar herramientas externas (Google Drive, Gmail, browser, base de datos). Ya está configurado en tu setup |

---

*Última actualización: 2026-05-25 · Hermes Stack · erikjosehrnndz-crypto*
