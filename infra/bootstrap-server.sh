#!/bin/bash
# bootstrap-server.sh - Preparacion inicial del VPS
# Ejecutar como root en instalacion limpia de Ubuntu 24.04 LTS
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "==> 1. Actualizando paquetes del sistema..."
apt-get update && apt-get upgrade -y

echo "==> 2. Instalando utilidades basicas..."
apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  software-properties-common \
  fail2ban \
  ufw \
  htop \
  ncdu \
  jq \
  git

echo "==> 3. Configurando repositorio y llaves de Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

echo "==> 4. Instalando Docker Engine y Docker Compose..."
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> 5. Configurando Docker Daemon (Log rotation y Live Restore)..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "default-ulimits": {
    "nofile": {
      "name": "nofile",
      "hard": 64000,
      "soft": 64000
    }
  }
}
EOF

systemctl daemon-reload
systemctl restart docker

echo "==> 6. Instalando Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh

echo "================================================================="
echo "Bootstrap completado exitosamente."
echo "Para iniciar Tailscale ejecuta: tailscale up --ssh --accept-routes"
echo "================================================================="
