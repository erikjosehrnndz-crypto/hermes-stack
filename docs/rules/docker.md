# Reglas — Docker

## Nombres de servicio vs contenedor

Para `docker compose up --no-deps`, usar el **nombre de servicio**, no el de contenedor:

| Servicio (`docker compose`) | Contenedor (`docker inspect`) |
|---|---|
| `litellm` | `litellm-router` |
| `hermes` | `hermes-agent` |
| `whisper-stt` | `whisper-stt` |

El watchdog y cualquier script con `docker compose up --no-deps <servicio>` usa el nombre de servicio.

## Healthcheck — usar `127.0.0.1`, no `localhost`

`localhost` en contenedores Alpine puede resolver a `[::1]` (IPv6) mientras el proceso escucha en IPv4 → `Connection refused` aunque el servicio esté up.

```yaml
test: ["CMD", "wget", "--spider", "http://127.0.0.1:3000/api/health"]  # ✓
```

Previene healthcheck always-failing que oculta el estado real.

## Env vars entre servicios dependientes — copiar del servicio fuente

Al añadir un servicio que llama a otro, copiar las env vars relevantes en docker-compose.yml. No asumir disponibilidad por red compartida.

Previene `KeyError: 'LITELLM_MASTER_KEY'` en cron jobs de brain-worker que llaman a litellm.

## Servicios con imagen compartida — reconstruir TODOS al mismo tiempo

`brain` y `brain-worker` comparten Dockerfile y source. Un fix Python requiere `docker compose build brain brain-worker`. Reconstruir solo uno deja el otro con el error anterior.
