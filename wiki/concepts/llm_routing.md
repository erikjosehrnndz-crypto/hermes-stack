---
name: "LLM Routing"
type: "concept"
category: "architecture"
status: "active"
introduced_date: "2026-03-15"
last_reviewed: "2026-05-25"
---

# LLM Routing

LiteLLM actúa como capa de abstracción entre [[hermes_agent]] y los proveedores de modelos de lenguaje externos. Recibe requests en un formato unificado y los enruta al proveedor correcto según disponibilidad y política de fallback.

## Por qué existe

El Hermes Stack necesita poder cambiar de modelo LLM sin modificar el código del agente. Distintos proveedores tienen distintas APIs, formatos de request/response y tiempos de respuesta. LiteLLM normaliza esta heterogeneidad: el agente siempre llama al mismo endpoint (`:4000`) con el mismo formato, y el router decide a quién llamar.

Además, ningún proveedor tiene 100% de uptime. Una política de fallback automático reduce los cortes de servicio cuando un proveedor falla.

## Cómo funciona

### Arquitectura

```
[[hermes_agent]]
    ↓  POST /chat/completions (OpenAI-compatible)
[[litellm_router]]  — :4000
    ↓  enrutamiento según config
┌─────────┬──────────────┐
OpenRouter         Gemini
(modelos Claude,   (Google AI)
 GPT, Mixtral...)
```

### Configuración y autenticación

- El router expone una API compatible con OpenAI en `:4000`.
- Todas las llamadas al health check requieren el header `Authorization: Bearer $LITELLM_MASTER_KEY`.
- Las claves de proveedores (OpenRouter API key, Gemini API key) se configuran en `.env` y se pasan al contenedor.

### Política de fallback

Si el proveedor primario no responde o retorna error, LiteLLM puede configurarse para reintentar con un proveedor secundario. La estrategia exacta está en la config de LiteLLM (no documentada aquí — consultar la config del contenedor).

### Health check

```bash
source /root/.env
curl -f -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
```

Este comando verifica que el router esté levantado y pueda contactar a los proveedores configurados.

## Entidades relacionadas

- [[litellm_router]] — la entidad concreta que implementa este concepto
- [[hermes_agent]] — consumidor del router
- [[voice_pipeline_e2e]] — el pipeline donde este concepto es crítico
- [[ci_cd_pipeline]] — el health check de LiteLLM es parte del pipeline de deploy

## Trade-offs

- **Ganado:** abstracción de proveedores, fallback automático, formato unificado OpenAI-compatible, monitoreo centralizado de llamadas LLM.
- **Perdido:** un hop extra en latencia (proceso adicional en la ruta), complejidad de configuración, dependencia en LiteLLM como proyecto externo.

## Evolución

- Se añadió autenticación al health check (antes era unauthenticated, lo que causaba falsos resultados en el CI/CD).
- Gemini se incorporó como proveedor alternativo a OpenRouter para diversificar la política de fallback.

## Referencias

- [[deployment_workflow]] — verificar health check de LiteLLM como paso obligatorio post-deploy
- [[voice_pipeline_e2e]] — contexto del pipeline donde este router es nodo central
