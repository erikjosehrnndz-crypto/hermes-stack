---
name: "Docker Network Isolation"
type: concept
category: architecture
status: active
introduced_date: "2026-03-01"
last_reviewed: "2026-05-25"
---

# Docker Network Isolation

El Hermes Stack usa dos redes Docker internas para separar el trafico funcional del trafico de observabilidad: `backend` para servicios del stack, `monitoring` para Prometheus, Grafana y exporters.

## Por que existe

Sin aislamiento de redes, un servicio de observabilidad comprometido o con un bug podria interferir con el trafico funcional. La separacion tambien reduce la superficie de ataque: los servicios de metricas no pueden comunicarse directamente con los servicios funcionales a menos que sean explicitamente anadidos a ambas redes.

## Como funciona

### Red `backend`

Contiene todos los servicios funcionales del stack:
- [[hermes_agent]], [[litellm_router]], [[whisper_stt]], [[redis]], [[hermes_website]], [[filebrowser]], [[caddy]]

### Red `monitoring`

Contiene los servicios de observabilidad:
- [[prometheus]], [[grafana]], cadvisor, node-exporter

### Regla de asignacion

- **Servicios funcionales** → red `backend`
- **Servicios de observabilidad** → red `monitoring`
- [[caddy]] esta en `backend` y actua como reverse proxy externo

Los puertos se bindean a `127.0.0.1:PUERTO` (localhost), nunca a `0.0.0.0` para servicios internos. Caddy es el unico punto de entrada desde el exterior.

## Entidades relacionadas

- [[caddy]] — reverse proxy externo, en red backend
- [[prometheus]] — en red monitoring
- [[grafana]] — en red monitoring
- [[redis]] — en red backend, solo interna
- [[docker_compose_stack]] — definicion de redes en docker-compose.yml

## Trade-offs

- **Ganado:** aislamiento de trafico, reduccion de superficie de ataque, claridad conceptual sobre que servicios son funcionales vs de observabilidad.
- **Perdido:** mayor complejidad al anadir servicios que necesitan estar en ambas redes.

## Referencias

- [[adding_new_service]] — al anadir un servicio, decidir a que red pertenece
- [[docker_compose_stack]] — tabla de servicios y sus redes
