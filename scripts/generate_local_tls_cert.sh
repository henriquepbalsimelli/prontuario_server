#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="deploy/nginx/certs"
CERT_FILE="${CERT_DIR}/local.crt"
KEY_FILE="${CERT_DIR}/local.key"

mkdir -p "${CERT_DIR}"

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "${KEY_FILE}" \
  -out "${CERT_FILE}" \
  -subj "/C=BR/ST=SP/L=SaoPaulo/O=Prontuario/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Generated ${CERT_FILE} and ${KEY_FILE}"
