---
name: "Docker Compose Stack"
type: "concept"
category: "architecture"
status: "active"
introduced_date: "2026-03-01"
last_reviewed: "2026-05-25"
---

# Docker Compose Stack

El Hermes Stack se orquesta mediante Docker Compose: 10 servicios definidos en `docker-compose.yml`, corriendo en un VPS único bajo el dominio `el80.space`. La configuración centralizada permite levantar, detener y reconstruir cualquier combinación de servicios con un solo comando.

## Por qué existe

Un VPS único con 10 microservicios necesita un mecanismo de orquestación que sea reproducible, declarativo y manejable sin Kubernetes. Docker Compose cubre este requisito para una escala de VPS único: define dependencias entre servicios, redes, volúmenes y políticas de reinicio en un solo archivo YAML.

## Cómo funciona

### Servicios activos

| Servicio (compose) | Contenedor (docker inspect) | Puerto host | Subdominio |
|---|---|---|---|
| `hermes` | `hermes-agent` | `127.0.0.1:8080` | `hermes.el80.space` |
| `litellm` | `litellm-router` | `127.0.0.1:4000` | `litellm.el80.space` |
| `grafana` | `grafana` | `127.0.0.1:3000` | `grafana.el80.space` |
| `website` | `hermes-website` | `127.0.0.1:3001` | `docs.el80.space` |
| `filebrowser` | `filebrowser` | `127.0.0.1:8095` | `files.el80.space` |
| `whisper-stt` | `whisper-stt` | `127.0.0.1:9000` | interno |
| `prometheus` | `prometheus` | `127.0.0.1:9090` | interno |
| `redis` | `redis` | interno | interno |
| `cadvisor` | `cadvisor` | interno | interno |
| `node-exporter` | `node-exporter` | interno | interno |

### Distinción crítica: nombre de servicio vs nombre de contenedor

Esta distinción es relevante para `docker compose up --no-deps`:

- `docker compose up --no-deps litellm` — usa nombre de **servicio** (`litellm`)
- `docker inspect litellm-router` — usa nombre de **contenedor** (`litellm-router`)

Confundir los dos nombres es una fuente de errores en scripts y el watchdog.

### Redes Docker

- **backend:** red interna para comunicación entre servicios funcionales (hermes, litellm, whisper, redis, website)
- **monitoring:** red interna para observabilidad (prometheus, grafana, cadvisor, node-exporter)

[[caddy]] actúa como reverse proxy externo y enruta hacia los puertos `127.0.0.1:*` de los servicios públicos.

### Comandos clave

```bash
# Estado de todos los servicios
docker compose ps

# Levantar stack completo (rebuild)
docker compose up -d --build

# Levantar un solo servicio sin sus dependencias
docker compose up --no-deps -d <nombre_servicio>

# Logs de un servicio
docker compose logs -f <nombre_servicio>

# Reiniciar un servicio
docker compose restart <nombre_servicio>
```

## Entidades relacionadas

- [[hermes_agent]] — agente conversacional, servicio `hermes`
- [[litellm_router]] — proxy LLM, servicio `litellm`
- [[whisper_stt]] — STT, servicio `whisper-stt`
- [[redis]] — cache, servicio `redis`
- [[prometheus]] — métricas, servicio `prometheus`
- [[grafana]] — dashboards, servicio `grafana`
- [[caddy]] — reverse proxy, gestiona TLS y subdominios
- [[hermes_website]] — frontend Next.js, servicio `website`
- [[filebrowser]] — gestor de archivos, servicio `filebrowser`
- [[ci_cd_pipeline]] — el pipeline usa `docker compose up -d --build` en cada deploy

## Trade-offs

- **Ganado:** orquestación simple en VPS único, sin overhead de Kubernetes, reproducibilidad total con un archivo YAML.
- **Perdido:** no hay escalado horizontal automático, no hay scheduling avanzado. Todo corre en el mismo host.

## Evolución

- Se agregó el servicio `website` (hermes-website, :3001) en sesión 2026-05-23 para exponer el frontend Next.js.
- La distinción nombre-servicio vs nombre-contenedor fue documentada después de errores en el watchdog.

## Referencias

- [[adding_new_service]] — checklist para añadir un nuevo servicio al compose
- [[deployment_workflow]] — flujo completo de deploy
- [[ci_cd_pipeline]] — cómo el CI/CD reconstruye el stack
