El siguiente paso es: completar mesh Tailscale (hs-007) — autenticar DO droplet (URL pendiente) y verificar Android (xiaomi-14t-pro offline).

**Trabajo completado en sesión 2026-05-26:**
- hs-001..hs-006: todos done (ver PENDIENTES.json)
- debug+optimización hermes: fallback session, deque history, tenacity retry, TTL 300s, async log
- Next.js: force-dynamic en 4 routes, deps muertas removidas (-52 paquetes)
- Redis: persistencia AOF + maxmemory 256mb allkeys-lru + volumen redis_data

**Commits clave:** `4f2540d` (stack fixes), `762fc61` (hs-006 merge), `7985863` (debug+opt)

**Credenciales control-center:**
- SSH Droplet: `ssh -i /root/.ssh/do_droplet_key root@104.236.74.0`
- Grafana: admin / HermesControl2026!
- Compose en Droplet: `/root/control-center/`
