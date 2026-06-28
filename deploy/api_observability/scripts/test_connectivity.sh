#!/usr/bin/env bash
set -uo pipefail

if [[ ! -f .env.alloy ]]; then
  echo "Arquivo .env.alloy nao encontrado em $(pwd)"
  exit 1
fi

source .env.alloy

GRPC_PORT="${ALLOY_HOST_OTLP_GRPC_PORT:-4317}"
HTTP_PORT="${ALLOY_HOST_OTLP_HTTP_PORT:-4318}"
TLS_INSECURE_SKIP_VERIFY="${ALLOY_EXPORT_TLS_INSECURE_SKIP_VERIFY:-false}"
export GRPC_PORT HTTP_PORT

normalize_host_endpoint() {
  local url="$1"
  if [[ "$url" == *"host.docker.internal"* ]]; then
    echo "${url//host.docker.internal/localhost}"
    return
  fi
  echo "$url"
}

LOKI_CHECK_URL="$(normalize_host_endpoint "${ALLOY_LOKI_WRITE_URL%/loki/api/v1/push}/loki/api/v1/labels")"
MIMIR_CHECK_URL="$(normalize_host_endpoint "${ALLOY_MIMIR_OTLP_HTTP_ENDPOINT%/otlp}/prometheus/api/v1/status/buildinfo")"
TEMPO_CHECK_URL="$(normalize_host_endpoint "${ALLOY_TEMPO_OTLP_HTTP_ENDPOINT%/v1/traces}/ready")"

failures=0

ok() {
  echo "OK"
}

fail() {
  echo "FALHOU: $1"
  failures=$((failures + 1))
}

curl_check() {
  if [[ "${TLS_INSECURE_SKIP_VERIFY}" == "true" ]]; then
    curl -kfsS -o /dev/null "$1"
    return
  fi

  curl -fsS -o /dev/null "$1"
}

echo "[1/5] Validando porta local OTLP gRPC no Alloy (${GRPC_PORT})"
if python3 - <<'PY'
import socket
import os
s = socket.socket()
s.settimeout(2)
s.connect(("127.0.0.1", int(os.environ.get("GRPC_PORT", "4317"))))
print("OK")
s.close()
PY
then
  :
else
  fail "Alloy nao esta escutando em 127.0.0.1:${GRPC_PORT}."
fi

echo "[2/5] Validando porta local OTLP HTTP no Alloy (${HTTP_PORT})"
if python3 - <<'PY'
import socket
import os
s = socket.socket()
s.settimeout(2)
s.connect(("127.0.0.1", int(os.environ.get("HTTP_PORT", "4318"))))
print("OK")
s.close()
PY
then
  :
else
  fail "Alloy nao esta escutando em 127.0.0.1:${HTTP_PORT}."
fi

echo "[3/5] Validando endpoint Loki write"
if curl_check "${LOKI_CHECK_URL}"; then
  ok
else
  fail "Loki indisponivel em ${LOKI_CHECK_URL}"
fi

echo "[4/5] Validando endpoint Mimir"
if curl_check "${MIMIR_CHECK_URL}"; then
  ok
else
  fail "Mimir indisponivel em ${MIMIR_CHECK_URL}"
fi

echo "[5/5] Validando endpoint Tempo"
if curl_check "${TEMPO_CHECK_URL}"; then
  ok
else
  echo "WARN: Tempo pode nao expor /ready no endpoint de ingestao (${ALLOY_TEMPO_OTLP_HTTP_ENDPOINT})."
fi

if [[ "$failures" -gt 0 ]]; then
  echo
  echo "Conectividade com falhas: ${failures} problema(s) encontrado(s)."
  echo "Dica: se API e LGTM estao em servidores diferentes, nao use localhost para Loki/Tempo/Mimir no .env.alloy."
  exit 1
fi

echo
echo "Conectividade basica validada."
