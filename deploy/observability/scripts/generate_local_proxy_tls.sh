#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="deploy/observability/proxy/certs"
FULLCHAIN_FILE="${CERT_DIR}/fullchain.pem"
PRIVKEY_FILE="${CERT_DIR}/privkey.pem"

mkdir -p "${CERT_DIR}"

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "${PRIVKEY_FILE}" \
  -out "${FULLCHAIN_FILE}" \
  -subj "/C=BR/ST=SP/L=SaoPaulo/O=Prontuario/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:grafana.localtest.me,DNS:otlp-http.localtest.me,DNS:otlp-grpc.localtest.me,DNS:mimir-otlp.localtest.me,DNS:loki-write.localtest.me,IP:127.0.0.1"

echo "Generated ${FULLCHAIN_FILE} and ${PRIVKEY_FILE}"
