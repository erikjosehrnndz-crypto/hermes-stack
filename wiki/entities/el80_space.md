---
name: el80.space
type: domain
status: active
port: N/A
domain: el80.space
port_name: N/A
docker_network: N/A
health_check_endpoint: N/A
last_updated: 2026-05-25
---

# el80.space

Dominio principal del Hermes Stack. Todos los servicios publicos del stack son accesibles bajo subdominios de `el80.space`, gestionados por [[caddy]] con TLS automatico via Let's Encrypt.

## Configuracion clave

- **DNS:** Apunta a la IP del VPS unico
- **TLS:** Certificados Let's Encrypt gestionados por [[caddy]]
- **Subdominios activos:**
  - `hermes.el80.space` → [[hermes_agent]] :8080
  - `litellm.el80.space` → [[litellm_router]] :4000
  - `grafana.el80.space` → [[grafana]] :3000
  - `docs.el80.space` → [[hermes_website]] :3001
  - `files.el80.space` → [[filebrowser]] :8095

## Relaciones

- Todos los subdominios enrutados por: [[caddy]]
- Servicios detras del dominio: [[hermes_agent]], [[litellm_router]], [[grafana]], [[hermes_website]], [[filebrowser]]
- Pipeline CI/CD despliega a: VPS donde corre este dominio

## Health check

```bash
# Verificar que el dominio resuelve al VPS
dig el80.space

# Verificar HTTPS en un subdominio
curl -f https://hermes.el80.space/health
```

## Runbook

Si un subdominio no responde:
1. Verificar que el servicio Docker este arriba: `docker compose ps`
2. Verificar que Caddy tenga el bloque configurado: `docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile`
3. Verificar DNS: `dig <subdominio>.el80.space` debe apuntar a IP del VPS
4. Ver logs de Caddy: `docker compose logs -f caddy`

## Referencias

- [[caddy]] — reverse proxy que gestiona todos los subdominios
- [[https_git_push]] — el VPS donde vive este dominio
- [[ci_cd_pipeline]] — el deploy va al VPS de este dominio
