#!/bin/bash
# docker-tailscale-iptables.sh - Restringir acceso Docker a Tailscale
set -euo pipefail

echo "==> Configurando reglas IPTables para aislar Docker..."

# Asegurar que el directorio de iptables-persistent existe
mkdir -p /etc/iptables

# Limpiar reglas anteriores en la cadena DOCKER-USER para evitar duplicados
# (Ignoramos el error si no hay reglas que limpiar)
iptables -D DOCKER-USER -i tailscale0 -j ACCEPT 2>/dev/null || true
iptables -D DOCKER-USER -i lo -j ACCEPT 2>/dev/null || true
iptables -D DOCKER-USER -i eth0 -j DROP 2>/dev/null || true
iptables -D DOCKER-USER -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true

# Permitir conexiones ya establecidas o relacionadas
iptables -I DOCKER-USER -m state --state ESTABLISHED,RELATED -j ACCEPT

# Permitir trafico desde la interfaz Tailscale
iptables -I DOCKER-USER -i tailscale0 -j ACCEPT

# Permitir trafico loopback (comunicacion local)
iptables -I DOCKER-USER -i lo -j ACCEPT

# Denegar todo el trafico externo de entrada por interfaces de red publicas comunes
iptables -A DOCKER-USER -i eth0 -j DROP
iptables -A DOCKER-USER -i ens+ -j DROP
iptables -A DOCKER-USER -i enp+ -j DROP

# Guardar reglas persistentes
echo "==> Guardando reglas de IPTables..."
if command -v iptables-save >/dev/null 2>&1; then
  iptables-save > /etc/iptables/rules.v4
  echo "Reglas guardadas en /etc/iptables/rules.v4"
else
  echo "ADVERTENCIA: iptables-save no esta instalado, no se pudo persistir las reglas de forma automatica."
fi
