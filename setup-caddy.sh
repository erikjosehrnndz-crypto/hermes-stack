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

echo "==> 4. Configurando Caddyfile para el80.space..."
cat > /etc/caddy/Caddyfile <<'EOF'
# Configuración de subdominios para el80.space
# Caddy gestionará los certificados SSL (HTTPS) automáticamente con Let's Encrypt

hermes.el80.space {
    reverse_proxy 127.0.0.1:8080
}

litellm.el80.space {
    reverse_proxy 127.0.0.1:4000
}

grafana.el80.space {
    reverse_proxy 127.0.0.1:3000
}
EOF

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
echo "================================================================"
