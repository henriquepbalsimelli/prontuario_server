#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Uso: $0 <grafana_user> <grafana_pass> <otlp_user> <otlp_pass>"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTH_DIR="${SCRIPT_DIR}/../proxy/auth"

mkdir -p "${AUTH_DIR}"

GRAFANA_USER="$1"
GRAFANA_PASS="$2"
OTLP_USER="$3"
OTLP_PASS="$4"

printf "%s:%s\n" "${GRAFANA_USER}" "$(openssl passwd -apr1 "${GRAFANA_PASS}")" > "${AUTH_DIR}/grafana.htpasswd"
printf "%s:%s\n" "${OTLP_USER}" "$(openssl passwd -apr1 "${OTLP_PASS}")" > "${AUTH_DIR}/otlp.htpasswd"

echo "Arquivos gerados:"
echo "- ${AUTH_DIR}/grafana.htpasswd"
echo "- ${AUTH_DIR}/otlp.htpasswd"
