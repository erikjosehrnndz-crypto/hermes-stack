---
name: Grafana
type: service
status: active
port: 3000
domain: grafana.el80.space
port_name: grafana
docker_network: monitoring
health_check_endpoint: GET /api/health
last_updated: 2026-05-25
---

# Grafana

Plataforma de visualización de métricas y dashboards. Conecta con [[prometheus]] para mostrar estado en tiempo real de latencia, throughput, errores y recursos.

## Configuración clave

- **Puerto host:** 127.0.0.1:3000
- **Imagen Docker:** grafana/grafana
- **Red Docker:** monitoring
- **Red externa:** Expuesto vía [[caddy]] en grafana.el80.space
- **Credenciales por defecto:** admin / admin (cambiar en producción)
- **Data source:** Prometheus (localhost:9090)

## Relaciones

- Consume: [[prometheus]] (métricas)
- Sirve a: [[caddy]] (HTTP/HTTPS)
- Implementa: [[observability_stack]]

## Health check

```bash
curl -f http://127.0.0.1:3000/api/health
```

Respuesta esperada: `{"database": "ok", ...}` (200)

## Runbook

### Inicio

```bash
docker compose up -d grafana
```

### Restart

```bash
docker compose restart grafana
```

### Logs

```bash
docker compose logs -f grafana
```

### Acceso web

Desde navegador en el VPS:
- **Localmente:** http://127.0.0.1:3000
- **Público:** https://grafana.el80.space (requiere [[caddy]])

Default login: `admin / admin`

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Datasource rojo (no conecta) | "Datasource error: connection refused" | Verificar que [[prometheus]] esté up: `docker compose ps prometheus` |
| Dashboards vacíos | Gráficos sin datos | Confirmar que Prometheus tenga métricas: `curl http://127.0.0.1:9090/api/v1/query?query=up` |
| Credenciales olvidadas | No puede loguearse | Resettear admin en BD: `docker compose exec grafana grafana-cli admin reset-admin-password newpass` |
| UI lento | Dashboards tardan mucho | Aumentar `evaluation_interval` en [[prometheus]] o reducir densidad de paneles |

## Dashboards disponibles

1. **Hermes Agent** — latencia, throughput, errores
2. **LiteLLM Usage** — fallback rate, costos, latencia por modelo
3. **Infrastructure** — CPU, memory, disk (via cadvisor)

## Referencias

- [[observability_stack]] — arquitectura de observabilidad
- Dockerfile: `grafana/Dockerfile`
- Dashboards: `grafana/provisioning/dashboards/`
- [[prometheus]] — fuente de datos
