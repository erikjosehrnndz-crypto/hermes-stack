---
name: "LLM Fallback Strategy"
type: concept
category: architecture
status: active
introduced_date: "2026-03-15"
last_reviewed: "2026-05-25"
---

# LLM Fallback Strategy

La estrategia de fallback de LLM define que hace [[litellm_router]] cuando un proveedor primario (OpenRouter) no responde o retorna error. El fallback automatico a Gemini reduce el impacto de interrupciones de proveedores externos.

## Por que existe

Ningun proveedor LLM externo tiene 100% de uptime. Sin fallback, un corte de OpenRouter detendria completamente el pipeline de voz del Hermes Stack. La estrategia de fallback permite continuar operando con degradacion graceful.

## Como funciona

[[litellm_router]] actua como orquestador de proveedores:

```
[[hermes_agent]] → POST /chat/completions
    ↓
[[litellm_router]]
    ├── Intento 1: OpenRouter (modelos Claude, GPT, Mixtral)
    │       ↓ (si error 5xx, timeout, o rate limit)
    └── Intento 2: Gemini (Google AI)
```

La configuracion exacta de reintentos, timeouts y modelos esta en `litellm/config.yaml`.

## Entidades relacionadas

- [[litellm_router]] — implementa la estrategia de fallback
- [[hermes_agent]] — consumidor que no necesita saber sobre el fallback
- [[voice_pipeline_e2e]] — el pipeline donde este concepto es critico para el SLO de 500ms

## Trade-offs

- **Ganado:** resiliencia ante fallos de un proveedor, diversificacion de dependencias externas.
- **Perdido:** latencia adicional cuando ocurre el fallback (el tiempo de timeout del proveedor primario se suma), costos distintos entre proveedores.

## Evolucion

- Gemini se incorporo como alternativa a OpenRouter para diversificar.
- La autenticacion del health check se anadio para verificar la conectividad real con los proveedores.

## Referencias

- [[llm_routing]] — arquitectura completa del router LLM
- [[litellm_router]] — entidad que implementa la estrategia
- [[voice_pipeline_e2e]] — contexto critico donde aplica el fallback
