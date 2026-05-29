# Reglas — Stack de producción (referencia)

| Parámetro | Valor |
|---|---|
| Directorio raíz VPS | `/root` |
| Dominio base | `el80.space` |
| Repositorio | `github.com/erikjosehrnndz-crypto/hermes-stack` |
| Contenedores activos | 10 |
| Latencia E2E objetivo | < 500 ms |

## Mapa de servicios y puertos

| Servicio | Puerto host | Subdominio |
|---|---|---|
| hermes-agent | `127.0.0.1:8080` | `hermes.el80.space` |
| litellm-router | `127.0.0.1:4000` | `litellm.el80.space` |
| grafana | `127.0.0.1:3000` | `grafana.el80.space` |
| hermes-website | `127.0.0.1:3001` | `docs.el80.space` |
| filebrowser | `127.0.0.1:8095` | `files.el80.space` |
| couchdb-obsidian | `127.0.0.1:5984` | `livesync.el80.space` |
| whisper-stt | `127.0.0.1:9000` | — interno |
| prometheus | `127.0.0.1:9090` | — interno |

## Health check post-deploy

```bash
source /root/.env
curl -f -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://127.0.0.1:4000/health
curl -f http://127.0.0.1:8080/health
```

Siempre verificar antes de declarar un deploy exitoso.

> Nota: `couchdb-obsidian`/`livesync` quedó como infra dormida tras migrar a Obsidian Sync. Pendiente de teardown según decisión del usuario.
