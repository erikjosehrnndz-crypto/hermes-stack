---
name: "Adding a New Service"
type: "topic"
difficulty: "intermediate"
time_estimate: "20-40 min"
involves: ["docker_compose_stack", "caddy", "prometheus", "ci_cd_pipeline"]
last_updated: "2026-05-25"
---

# Adding a New Service

En una línea: checklist completo para añadir un nuevo contenedor Docker al [[docker_compose_stack]].

## Por qué importa

Añadir un servicio sin seguir este checklist puede resultar en: el servicio no arrancando, no siendo accesible desde el exterior, no siendo monitorizado, o exponiendo secretos al repositorio.

## Pasos

### 1. Definir el servicio en `docker-compose.yml`

```yaml
nuevo-servicio:
  image: imagen:tag
  container_name: nuevo-servicio
  restart: unless-stopped
  networks:
    - backend          # o monitoring si es servicio de observabilidad
  ports:
    - "127.0.0.1:XXXX:XXXX"   # siempre bind a localhost, nunca 0.0.0.0
  environment:
    - VARIABLE=${VARIABLE}     # referencias a .env, no valores en texto plano
  depends_on:
    - redis            # si aplica
```

Notas críticas:
- El puerto debe ser `127.0.0.1:HOST:CONTAINER` — nunca `0.0.0.0:PORT:PORT` para servicios internos.
- Las variables de entorno sensibles van en `.env`, nunca hardcodeadas en el compose.
- El nombre del **servicio** (clave YAML) y el **contenedor** (`container_name`) pueden ser distintos — documentar ambos en [[docker_compose_stack]].

### 2. Añadir variables de entorno al `.env`

```bash
# En /root/.env
NUEVA_VARIABLE=valor_secreto
```

Nunca commitear `.env` al repositorio.

### 3. Configurar subdominio en Caddy (si el servicio es público)

Editar `setup-caddy.sh` o el Caddyfile para añadir el bloque del nuevo subdominio:

```
nuevo.el80.space {
    reverse_proxy 127.0.0.1:XXXX
}
```

Recargar Caddy después del cambio:
```bash
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### 4. Actualizar `.gitignore` si el servicio genera artefactos

```bash
ls -la /root/<directorio-del-servicio>/
```

Añadir al `.gitignore` correspondiente cualquier `.db`, logs, archivos de estado runtime.

### 5. Añadir health check al CI/CD

Editar `.github/workflows/deploy.yml` para incluir un health check del nuevo servicio:

```yaml
- name: Health check nuevo servicio
  run: curl -f http://127.0.0.1:XXXX/health
```

Leer el workflow actual antes de modificarlo:
```bash
cat /root/.github/workflows/deploy.yml
```

### 6. Configurar monitoreo (si aplica)

Si el servicio expone métricas Prometheus:
- Añadir un scrape job en la config de [[prometheus]].
- Crear un panel en [[grafana]] para las métricas nuevas.

### 7. Levantar y verificar

```bash
# Levantar solo el nuevo servicio
docker compose up --no-deps -d <nombre_servicio>

# Verificar que arrancó
docker compose ps

# Ver logs
docker compose logs -f <nombre_servicio>
```

### 8. Commitear y hacer deploy

Seguir [[deployment_workflow]] completo, incluyendo verificación de health checks post-deploy.

### 9. Documentar en la wiki

Crear `wiki/entities/<nombre_servicio>.md` con:
- Puerto y subdominio
- Dependencias
- Health check command
- Runbook básico

Actualizar `wiki/_index.md` para incluir la nueva entidad.

## Notas

- **Nombre servicio vs contenedor:** son claves distintas en docker-compose.yml. `docker compose up --no-deps` usa el nombre de **servicio** (clave YAML). `docker inspect` usa el nombre de **contenedor** (`container_name`). Ver [[docker_compose_stack]].
- **Redes:** servicios funcionales → red `backend`; servicios de observabilidad → red `monitoring`. No mezclar.
- **Antes de añadir un servidor HTTP separado en website/:** revisar si no es mejor implementarlo como Route Handler de Next.js. Ver [[nextjs_app_router]].

## Gotchas

- Olvidar `restart: unless-stopped` hace que el contenedor no arranque tras reboot del VPS.
- Bind a `0.0.0.0` en lugar de `127.0.0.1` expone el servicio directamente al exterior sin pasar por Caddy.
- Si el servicio genera una base de datos `.db`, añadirla al `.gitignore` antes del primer `git add`.

## Véase también

- [[docker_compose_stack]] — estado completo del stack y convenciones
- [[deployment_workflow]] — cómo desplegar el cambio una vez definido
- [[ci_cd_pipeline]] — pipeline que verifica el nuevo servicio en cada deploy
