---
name: "Voice Pipeline E2E"
type: "concept"
category: "architecture"
status: "active"
introduced_date: "2026-03-15"
last_reviewed: "2026-05-25"
slo_target: "< 500ms"
critical_path: ["whisper_stt", "hermes_agent", "litellm_router", "elevenlabs"]
---

# Voice Pipeline E2E

El pipeline de voz extremo a extremo convierte audio de micrófono en respuesta de audio sintetizada, pasando por transcripción, razonamiento conversacional, orquestación de LLMs y síntesis de voz. Es el flujo de datos más crítico del Hermes Stack.

## Por qué existe

El objetivo del stack es ser un asistente de IA conversacional autohospedado accesible por voz. Esto requiere integrar cuatro sistemas especializados: reconocimiento de voz, agencia conversacional, enrutamiento de modelos de lenguaje y síntesis de voz. El pipeline E2E es la composición de esos cuatro sistemas bajo un SLO de latencia de 500 ms.

## Cómo funciona

Flujo de datos completo:

```
Micrófono
    ↓  (audio stream)
[[whisper_stt]]  — :9000
    ↓  (texto transcrito)
[[hermes_agent]]  — :8080
    ↓  (prompt + contexto conversacional)
[[litellm_router]]  — :4000
    ↓  (request a proveedor)
OpenRouter / Gemini  — externo
    ↓  (respuesta LLM)
[[hermes_agent]]  — :8080
    ↓  (texto de respuesta)
ElevenLabs Flash v2.5  — WebSocket, externo
    ↓  (audio sintetizado)
Altavoz
```

Pasos clave:

1. **STT (Speech-to-Text):** [[whisper_stt]] recibe el stream de audio y retorna texto transcrito. Opera en red interna.
2. **Agencia:** [[hermes_agent]] recibe el texto, aplica contexto conversacional y construye el prompt para el LLM. Usa [[redis]] para estado de sesión.
3. **LLM Routing:** [[litellm_router]] recibe el request y lo enruta a OpenRouter o Gemini según disponibilidad y política de fallback.
4. **TTS (Text-to-Speech):** [[hermes_agent]] envía la respuesta del LLM a ElevenLabs Flash v2.5 vía WebSocket para síntesis en tiempo real.

## Entidades relacionadas

- [[whisper_stt]] — transcripción de audio a texto, puerto 9000
- [[hermes_agent]] — orquestación central del pipeline, puerto 8080
- [[litellm_router]] — proxy hacia proveedores LLM externos, puerto 4000
- [[redis]] — estado de sesión conversacional
- [[llm_routing]] — concepto de enrutamiento y fallback de LLMs

## Trade-offs

- **Ganado:** latencia baja con ElevenLabs Flash v2.5 (WebSocket streaming), privacidad de audio (Whisper local).
- **Perdido:** dependencia de ElevenLabs y OpenRouter/Gemini como servicios externos, puntos de fallo fuera del control del stack.

## Evolución

- El stack originalmente no tenía STT local; se agregó Whisper para mantener el audio en infraestructura propia.
- ElevenLabs Flash v2.5 reemplazó a versiones anteriores por menor latencia de síntesis.
- Roadmap: app Android nativa que consuma este pipeline directamente.

## Referencias

- [[deployment_workflow]] — cómo desplegar cambios en el pipeline
- [[llm_routing]] — estrategia de fallback en el router LLM
- [[docker_compose_stack]] — cómo se levantan los servicios del pipeline
