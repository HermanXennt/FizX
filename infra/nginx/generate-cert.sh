#!/bin/sh
# Generates a self-signed TLS cert for nginx, covering whatever hosts the
# deployment is actually reached by (LAN IP, localhost). Camera/microphone
# access (getUserMedia) is only available to "secure contexts" - https or
# localhost - so a LAN-IP deployment needs *some* cert even though there's
# no real domain to get one from a CA for. Browsers will show a one-time
# "connection is not private" warning to click through; that's expected for
# a self-signed cert and does not affect mediaDevices availability once
# accepted. Replace with a CA-issued cert (e.g. via a real domain + Let's
# Encrypt) for a deployment reachable from the public internet.
set -e

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

EXTRA_IP="${1:-}"
ALT_NAMES="DNS:localhost,IP:127.0.0.1"
if [ -n "$EXTRA_IP" ]; then
  ALT_NAMES="${ALT_NAMES},IP:${EXTRA_IP}"
fi

openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -subj "/CN=fizx.local" \
  -addext "subjectAltName=${ALT_NAMES}"

echo "Generated self-signed cert for: ${ALT_NAMES}"
echo "  ${CERT_DIR}/cert.pem"
echo "  ${CERT_DIR}/key.pem"
