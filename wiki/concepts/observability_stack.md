---
name: "Observability Stack"
type: concept
category: architecture
status: active
introduced_date: "2026-03-01"
last_reviewed: "2026-05-25"
---

# Observability Stack

El stack de observabilidad del Hermes Stack esta compuesto por Prometheus (recoleccion de metricas), Grafana (visualizacion y dashboards), cadvisor (metricas de contenedores) y node-exporter (metricas del host). Opera en una red Docker aislada (`monitoring`).

## Por que existe

Sin observabilidad, los problemas de latencia, error rate y consumo de recursos solo se detectan cuando el usuario los reporta. El stack permite monitorear en tiempo real el estado de todos los servicios, establecer alertas y diagnosticar problemas antes de que impacten al usuario.

## Como funciona

```
[[hermes_agent]] :8080/metrics ─┐
[[litellm_router]] :4000/metrics┤
[[whisper_stt]] :9000/metrics  ─┤
cadvisor (contenedores)        ─┤→ [[prometheus]] :9090 → [[grafana]] :3000
node-exporter (host)           ─┘
```

- **Prometheus** scrape metricas de todos los servicios cada 30s (configurable en `prometheus/prometheus.yml`).
- **Grafana** conecta con Prometheus como datasource y expone dashboards predefinidos.
- **cadvisor** exporta metricas de CPU, memoria y red por contenedor.
- **node-exporter** exporta metricas del host (CPU, disco, red).

## Entidades relacionadas

- [[prometheus]] — servidor de metricas, red monitoring, puerto 9090
- [[grafana]] — dashboards, red monitoring, puerto 3000
- [[hermes_agent]] — emite metricas de latencia y throughput
- [[litellm_router]] — emite metricas de uso de modelos y costos
- [[whisper_stt]] — emite metricas de latencia de transcripcion

## Trade-offs

- **Ganado:** visibilidad total del stack, alertas configurables, historial de metricas.
- **Perdido:** overhead de recursos (Prometheus + Grafana consumen CPU/memoria), complejidad de configuracion de dashboards.

## Evolucion

- El stack de observabilidad se configuro desde el inicio del proyecto.
- La red `monitoring` se separo de `backend` para aislar el trafico de metricas del trafico funcional.

## Referencias

- [[docker_compose_stack]] — como se integra en el compose
- [[deployment_workflow]] — health checks usan Prometheus implicitamente
