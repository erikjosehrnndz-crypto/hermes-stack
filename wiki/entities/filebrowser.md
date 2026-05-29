---
name: FileBrowser
type: service
status: active
port: 8095
domain: files.el80.space
port_name: filebrowser
docker_network: backend
health_check_endpoint: GET /
last_updated: 2026-05-25
---

# FileBrowser

Gestor de archivos web. Permite explorar, descargar, subir y editar archivos en el VPS a través de interfaz HTTP. Útil para administración de documentación, blueprints, y backups.

## Configuración clave

- **Puerto host:** 127.0.0.1:8095
- **Imagen Docker:** filebrowser/filebrowser
- **Red Docker:** backend
- **Red externa:** Expuesto vía [[caddy]] en files.el80.space
- **Directorio raíz:** `/root` (acceso a todo el proyecto)
- **Credenciales:** Configuradas en `filebrowser.db` (admin/admin por defecto)
- **Volumen DB:** `filebrowser.db` (sqlite, persistente)

## Relaciones

- Sirve a: [[caddy]]
- Acceso a: Todos los directorios del VPS (documentos, code, logs)
- Puede consultar: [[prometheus]] (métricas), logs de servicios

## Health check

```bash
curl -f http://127.0.0.1:8095/
```

Respuesta: HTML 200 (login page)

## Runbook

### Inicio

```bash
docker compose up -d filebrowser
```

### Restart

```bash
docker compose restart filebrowser
```

### Logs

```bash
docker compose logs -f filebrowser
```

### Acceso web

- **Localmente:** http://127.0.0.1:8095
- **Público:** https://files.el80.space (requiere [[caddy]])

Default login: `admin / admin`

### Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| No puede subir archivos | Error 413 (payload too large) | Aumentar límite en Caddy reverse_proxy o filebrowser config |
| Permisos denegados | Cannot read file | Verificar permisos del directorio: `chmod 755 /root/<dir>` |
| DB corrupta | Container no inicia | Resettear: `rm filebrowser.db && docker compose up -d filebrowser` |
| Lento navegando directorios grandes | UI congela | Limitar número de archivos mostrados, aumentar timeout |

## Notas de seguridad

- **Riesgo alto:** FileBrowser expone TODOS los archivos de `/root`
- **En producción:** Considerar limitar a directorio específico (ej. `documents/`, `backups/`)
- **Credenciales:** Cambiar admin/admin en primer acceso
- **TLS:** Usar HTTPS siempre (requiere [[caddy]])

## Archivos notables accesibles

- `CLAUDE.md` — instrucciones del proyecto
- `Hermes_Stack_Blueprint.pdf` — documentación técnica
- `docker-compose.yml` — configuración de servicios
- `.env` — **SECRETO**, nunca exponerlo
- `website/` — código fuente del frontend

## Referencias

- [[docker_network_isolation]] — exposición de archivos en red backend
- Dockerfile: filebrowser/filebrowser (imagen oficial)
- Database: `filebrowser.db` (sqlite3)
