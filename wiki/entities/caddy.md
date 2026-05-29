---
name: Caddy
type: service
status: active
port: 80/443
domain: el80.space (configurador central)
port_name: caddy
docker_network: backend
health_check_endpoint: N/A (reverse proxy)
last_updated: 2026-05-25
---

# Caddy

Reverse proxy + servidor HTTP/HTTPS central. Enruta subdominios (hermes.el80.space, litellm.el80.space, docs.el80.space, etc.) a los servicios backend correspondientes. Maneja automáticamente certificados TLS vía Let's Encrypt.

## Configuración clave

- **Puertos host:** 127.0.0.1:80 (HTTP), 127.0.0.1:443 (HTTPS)
- **Imagen Docker:** caddy:latest
- **Red Docker:** backend (acceso a todos los servicios)
- **Archivo config:** `caddy/Caddyfile`
- **Volumen TLS:** `/data/caddy` (certificados Let's Encrypt)
- **Email ACME:** Configurado en Caddyfile global

## Relaciones

- Upstream: [[hermes_agent]], [[litellm_router]], [[hermes_website]], [[grafana]], [[filebrowser]]
- Todos los servicios públicos dependen de Caddy para HTTPS
- Implementa: [[zero_downtime_deploy]] (health checks antes de ruteo)

## Health check

Caddy no expone endpoint de health. Verificar routing:

```bash
# HTTP → HTTPS redirect
curl -i http://127.0.0.1/

# HTTPS (con cert self-signed en dev, Let's Encrypt en prod)
curl -k https://127.0.0.1/
```

## Configuración Caddyfile

Estructura típica:

```
{
  email admin@el80.space
}

hermes.el80.space {
  reverse_proxy 127.0.0.1:8080
}

litellm.el80.space {
  reverse_proxy 127.0.0.1:4000
}

docs.el80.space {
  reverse_proxy 127.0.0.1:3001
}

grafana.el80.space {
  reverse_proxy 127.0.0.1:3000
}

files.el80.space {
  reverse_proxy 127.0.0.1:8095
}
```

## Runbook

### Inicio

```bash
docker compose up -d caddy
```

### Restart

```bash
docker compose restart caddy
```

### Logs

```bash
docker compose logs -f caddy
```

### Reload de configuración (sin downtime)

```bash
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| 502 Bad Gateway | Upstream no responde | Verificar servicio target: `docker compose ps <servicio>` |
| TLS error (cert expirado) | Navegador: "SEC_ERROR_UNKNOWN_ISSUER" | Revisar volumen `/data/caddy` tiene permisos, Let's Encrypt acceso (es dev env?) |
| Subdomain no resuelve | DNS timeout | Verificar DNS configurado para el80.space apunta a IP del VPS |
| Slow HTTPS | Handshake lento | Revisar Caddy logs, aumentar timeout en reverse_proxy |

## Monitoreo

- **Certificados TLS:** Validez y fecha de renovación (Let's Encrypt)
- **Upstream health:** Estado de backends (200 OK)
- **Throughput:** Requests/sec a través del proxy

## Referencias

- [[zero_downtime_deploy]] — cómo Caddy facilita deployment sin downtime
- Dockerfile: caddy:latest (imagen oficial)
- Caddyfile: `caddy/Caddyfile`
- [[docker_network_isolation]] — por qué Caddy está en red backend
- Setup script: `setup-caddy.sh` (si existe)
