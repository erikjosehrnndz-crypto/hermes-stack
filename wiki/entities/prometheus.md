---
name: Prometheus
type: service
status: active
port: 9090
domain: interno
port_name: prometheus
docker_network: monitoring
health_check_endpoint: GET /-/healthy
last_updated: 2026-05-25
---

# Prometheus

Servidor de métricas de series temporales. Recolecta eventos y contadores de todos los servicios (hermes-agent, litellm-router, etc.), node-exporter, y cadvisor.

## Configuración clave

- **Puerto host:** 127.0.0.1:9090
- **Imagen Docker:** prom/prometheus
- **Red Docker:** monitoring (aislada del backend)
- **No expuesto públicamente:** Solo [[grafana]] accede
- **Archivo config:** `prometheus/prometheus.yml`
- **Volumen:** `/prometheus` (datos persistentes)
- **Scrape interval:** 30s (por defecto)

## Relaciones

- Scrape de: [[hermes_agent]], [[litellm_router]], [[whisper_stt]], cadvisor, node-exporter
- Alimenta a: [[grafana]] (visualización)
- Implementa: [[observability_stack]]

## Health check

```bash
curl -f http://127.0.0.1:9090/-/healthy
```

Respuesta esperada: `Prometheus is Healthy` (200)

## Runbook

### Inicio

```bash
docker compose up -d prometheus
```

### Restart

```bash
docker compose restart prometheus
```

### Logs

```bash
docker compose logs -f prometheus
```

### Acceso al Web UI

Localmente (en el VPS):
```bash
curl http://127.0.0.1:9090/api/v1/targets
```

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Targets en rojo (DOWN) | Prometheus no puede scrape | Verificar que servicio target esté up: `docker compose ps` |
| Métrica faltante | Query devuelve `no data` | Confirmar que aplicación emita métrica, revisar prometheus.yml |
| Disco lleno | Almacenamiento de datos falla | Aumentar `retention` en prometheus.yml o limpiar datos históricos |
| High memory | Prometheus consume >1GB RAM | Reducir `retention` o aumentar `scrape_interval` en yml |

## Métricas críticas a monitorear

- `http_request_duration_seconds` — latencia por servicio
- `http_requests_total` — throughput por servicio
- `http_request_errors_total` — errores por tipo
- `process_resident_memory_bytes` — memoria de cada servicio
- `process_cpu_seconds_total` — CPU utilizado

## Referencias

- [[observability_stack]] — arquitectura de observabilidad
- Dockerfile: `prometheus/Dockerfile`
- Config: `prometheus/prometheus.yml`
- Targets: `hermes-agent:8080/metrics`, `litellm:4000/metrics`, `whisper-stt:9000/metrics`
