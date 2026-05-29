#!/bin/bash
# setup-caddy.sh - Instala Caddy y configura HTTPS automatico para el80.space
set -euo pipefail

echo "==> 1. Instalando dependencias de Caddy..."
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl

echo "==> 2. Agregando repositorio oficial de Caddy..."
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list

echo "==> 3. Instalando Caddy..."
apt-get update
apt-get install -y caddy

echo "==> 4. Desplegando el Caddyfile canónico del repo (infra/Caddyfile)..."
# Fuente de verdad única: infra/Caddyfile (incluye hermes, litellm, grafana, docs,
# router, files, livesync, crm y el endpoint de métricas con basic_auth).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/Caddyfile" /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

echo "==> 5. Habilitando puertos 80 y 443 en el cortafuegos..."
ufw allow 80/tcp
ufw allow 443/tcp

echo "==> 6. Reiniciando y habilitando Caddy..."
systemctl daemon-reload
systemctl enable caddy
systemctl restart caddy

echo "================================================================"
echo "Caddy configurado exitosamente para el80.space!"
echo "Servicios expuestos en:"
echo "- https://hermes.el80.space  (Hermes Agent)"
echo "- https://litellm.el80.space (LiteLLM Router)"
echo "- https://grafana.el80.space (Grafana Metrics)"
echo "- https://docs.el80.space    (Hermes Website)"
echo "- https://syncthing.el80.space (Syncthing GUI)"
echo "- https://files.el80.space     (File Browser Web)"
echo "================================================================"
