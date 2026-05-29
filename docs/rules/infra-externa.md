# Reglas — Infraestructura externa

## Hostinger DNS

`https://developers.hostinger.com/api/dns/v1/zones/<dom>` (no `api.hostinger.com` → CF 530). PUT con `overwrite:false` añade sin borrar.

## SSL subdominio con wildcard `*→IP`

HTTP-01/TLS-ALPN-01 fallan por caché ACME. Usar DNS challenge:

```bash
~/.acme.sh/acme.sh --issue --dns dns_hostinger -d nuevo.el80.space --dnssleep 15
# key en HOSTINGER_API_KEY
```

## Digital Ocean

- Cuentas nuevas solo `s-*` (max $56/mes).
- `doctl` no preinstalado — descargar de `github.com/digitalocean/doctl/releases`.
- Control Center: `104.236.74.0`, SSH key `/root/.ssh/do_droplet_key`, compose en `/root/control-center/`.

## Caddy — config activa ≠ repo (editar AMBOS + reload)

Caddy corre por systemd leyendo **`/etc/caddy/Caddyfile`**, NO `/root/infra/Caddyfile`. El del repo está desincronizado (le faltan bloques `workspace`/`dashboard`/`brain`, e indenta con espacios mientras el repo usa tabs). Editar solo el repo **no surte efecto**.

Para añadir/cambiar un subdominio:
1. Editar `/etc/caddy/Caddyfile` (estilo espacios) — el que sirve.
2. Editar `/root/infra/Caddyfile` (estilo tabs) — para tracking en git.
3. `caddy validate --config /etc/caddy/Caddyfile` y `systemctl reload caddy`.

Previene un subdominio nuevo que devuelve cert/502 porque el cambio nunca llegó a la config activa.

## Tailscale

- `status` mostrando `active; offline` = sesión conocida pero nodo desconectado — verificar con `tailscale ping` antes de SSH.
- `tailscale up --advertise-tags=tag:infra --accept-routes` imprime URL de auth sin pre-generar key.
