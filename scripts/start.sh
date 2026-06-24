#!/bin/sh
# Detects this machine's current LAN IP and writes it into every place that
# needs to match it (.env's Django/LiveKit/coturn/MinIO settings, the nginx
# TLS cert's SAN) before bringing the stack up - so moving to a different
# WiFi/network doesn't silently break ICE candidates, the TURN relay,
# CORS/CSRF allowed origins, or trigger a cert mismatch.
#
# Usage: ./scripts/start.sh [docker compose args...]
#   ./scripts/start.sh              # detect IP, then `docker compose up -d`
#   ./scripts/start.sh --build      # detect IP, then `docker compose up -d --build`
set -e

cd "$(dirname "$0")/.."

ENV_FILE=.env

if [ ! -f "$ENV_FILE" ]; then
  echo "No $ENV_FILE found - copy .env.example to .env and fill in secrets first."
  exit 1
fi

detect_ip() {
  # Primary: IP of the interface the kernel would actually use to reach the
  # internet - reliable even with multiple interfaces/VPNs, and doesn't
  # require guessing which one is "the" LAN interface.
  ip route get 1.1.1.1 2>/dev/null | awk '/src/ {for (i=1; i<=NF; i++) if ($i == "src") print $(i+1)}' | head -n1
}

NEW_IP="$(detect_ip)"
if [ -z "$NEW_IP" ]; then
  # Fallback for environments without `ip route get` (e.g. some minimal
  # containers) - first address hostname -I reports.
  NEW_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
fi
if [ -z "$NEW_IP" ]; then
  echo "Could not auto-detect a LAN IP. Set LIVEKIT_NODE_IP etc. in $ENV_FILE manually."
  exit 1
fi

OLD_IP="$(grep -m1 '^LIVEKIT_NODE_IP=' "$ENV_FILE" | cut -d= -f2)"

set_env_var() {
  key="$1"
  value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    # Different sed delimiter (|) since the value contains slashes (URLs).
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

if [ "$OLD_IP" != "$NEW_IP" ]; then
  echo "LAN IP: ${OLD_IP:-<none yet>} -> ${NEW_IP}"

  set_env_var DJANGO_ALLOWED_HOSTS "localhost,127.0.0.1,${NEW_IP}"
  set_env_var DJANGO_CSRF_TRUSTED_ORIGINS "https://localhost,https://${NEW_IP}"
  set_env_var FRONTEND_URL "https://${NEW_IP}"
  set_env_var CORS_ALLOWED_ORIGINS "https://localhost,https://${NEW_IP}"
  set_env_var LIVEKIT_PUBLIC_URL "ws://${NEW_IP}:7880"
  set_env_var LIVEKIT_NODE_IP "${NEW_IP}"
  set_env_var TURN_PUBLIC_IP "${NEW_IP}"
  set_env_var AWS_S3_ENDPOINT_URL "http://${NEW_IP}:9000"

  ./infra/nginx/generate-cert.sh "${NEW_IP}"
  IP_CHANGED=1
else
  echo "LAN IP unchanged (${NEW_IP})."
  IP_CHANGED=0
fi

docker compose up -d "$@"

if [ "$IP_CHANGED" = "1" ]; then
  # These three either read the IP only at their own startup (nginx caches
  # the cert + upstream DNS once) or are the services whose advertised
  # address just changed (livekit/coturn) - everything else doesn't care.
  docker compose restart nginx livekit coturn
fi

echo ""
echo "Ready at https://${NEW_IP}"
