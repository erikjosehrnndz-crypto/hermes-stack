El siguiente paso es: resolver hs-001 (Hermes Agent: 0 requests en 47h — investigar pipeline Whisper → /process) o hacer merge de feat/nextjs-rocket-compat a main (hs-006).

**Trabajo completado en esta sesión (2026-05-26):**
- Creado Droplet DO `hermes-expansion` (104.236.74.0, NYC3, 4 vCPU / 8 GB)
- Desplegado Control Center: Grafana + Prometheus + Portainer en `https://control.el80.space`
- DNS `control.el80.space` añadido vía Hostinger API
- SSL emitido via DNS-01 (acme.sh), auto-renueva por cron
- Federación Prometheus configurada (agrega métricas del VPS principal)
- Hook DNS Hostinger instalado: `/root/.acme.sh/dnsapi/dns_hostinger.sh`

**Credenciales nuevas:**
- SSH Droplet: `ssh -i /root/.ssh/do_droplet_key root@104.236.74.0`
- Grafana: admin / HermesControl2026!
- Compose en Droplet: `/root/control-center/`
