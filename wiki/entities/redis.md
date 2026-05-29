---
name: Redis
type: service
status: active
port: 6379
domain: interno
port_name: redis
docker_network: backend
health_check_endpoint: PING (comando)
last_updated: 2026-05-25
---

# Redis

Cache distribuido y message broker. Almacena sesiones conversacionales de [[hermes_agent]] y actúa como cola para tareas asincrónicas.

## Configuración clave

- **Puerto host:** 127.0.0.1:6379
- **Imagen Docker:** redis:7-alpine
- **Red Docker:** backend (solo interna)
- **No expuesto públicamente:** Solo [[hermes_agent]] accede
- **Volumen:** `/data/redis` (persistencia RDB)
- **Configuración:** Defaults redis estándar

## Relaciones

- Alimentado por: [[hermes_agent]] (sesiones, estado conversacional)
- Consumido por: [[hermes_agent]] (cache de contexto)
- Implementa: [[docker_network_isolation]]

## Health check

```bash
docker compose exec redis redis-cli PING
```

Respuesta esperada: `PONG`

O desde host:

```bash
redis-cli -h 127.0.0.1 -p 6379 PING
```

## Runbook

### Inicio

```bash
docker compose up -d redis
```

### Restart

```bash
docker compose restart redis
```

### Logs

```bash
docker compose logs -f redis
```

### Acceso a CLI

```bash
redis-cli -h 127.0.0.1 -p 6379
> KEYS *                    # Listar todas las claves
> INFO stats                # Estadísticas
> FLUSHALL                  # Limpiar TODOS los datos (cuidado!)
> DBSIZE                    # Número de claves
```

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| No conecta | hermes-agent: "Connection refused" | Verificar que Redis esté up: `docker compose ps redis` |
| Memoria llena | Redis rechaza SETEX | Revisar política de eviction: `CONFIG GET maxmemory-policy` |
| Persistencia no funciona | Datos perdidos en restart | Verificar volumen existe: `docker volume ls | grep redis` |
| Latencia alta | SET/GET lento | Revisar tamaño de memoria, ejecutar `BGSAVE` para no bloquear |

## Monitoreo

- **keys_stored:** DBSIZE
- **memory_used:** INFO memory → used_memory_human
- **hits_vs_misses:** INFO stats → keyspace_hits / keyspace_misses

## Referencias

- [[docker_network_isolation]] — por qué Redis está en red backend
- Dockerfile: redis:7-alpine (imagen oficial)
- [[hermes_agent]] — consumidor principal
