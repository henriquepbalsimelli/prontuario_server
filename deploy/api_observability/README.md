# Fase 3 - Alloy no Servidor da API

Este diretório contém a base da Fase 3 para rodar o collector/agent (Grafana Alloy) no servidor da API.

## Escopo deste diretório
- Este compose (`docker-compose.alloy.yml`) deve rodar no servidor da API.
- O destino de logs/traces/métricas é o servidor de observabilidade (pasta `deploy/observability`).
- Em arquitetura com 2 servidores, `localhost` no Alloy sempre aponta para o servidor da API, nao para o servidor LGTM.
- No ambiente local deste projeto, as duas stacks compartilham a rede Docker externa `observability`; por isso o Alloy deve usar os nomes dos servicos Docker (`prontuario-tempo`, `prontuario-mimir`, `prontuario-loki`), nao `host.docker.internal`.

## O que está implementado
- Receiver OTLP local (`4317` gRPC e `4318` HTTP).
- Pipeline de traces -> Tempo.
- Pipeline de métricas -> Mimir (OTLP HTTP).
- Pipeline de logs (arquivo da API) -> Loki.
- Processadores de robustez (`memory_limiter`, `batch`) e fila/retry nos exporters OTel.

## Subir Alloy
```bash
cd deploy/api_observability
cp .env.alloy.example .env.alloy
docker compose -f docker-compose.alloy.yml up -d
```

## Verificar status
```bash
docker compose -f docker-compose.alloy.yml ps
docker compose -f docker-compose.alloy.yml logs --tail=100
```

## Validar conectividade básica
```bash
cd deploy/api_observability
./scripts/test_connectivity.sh
```

## Pontos de atenção
- A API deve apontar OTLP para `localhost:14317` (gRPC) ou `localhost:14318` (HTTP) quando estiver rodando no host.
- Se API e Alloy estiverem na mesma rede/container, pode usar `alloy:4317` ou `alloy:4318`.
- Se Alloy e LGTM estiverem na mesma rede Docker externa `observability`, use `http://prontuario-tempo:4318`, `http://prontuario-mimir:9009/otlp` e `http://prontuario-loki:3100/loki/api/v1/push`.
- Se houver conflito de porta local, ajustar `ALLOY_HOST_OTLP_GRPC_PORT` e `ALLOY_HOST_OTLP_HTTP_PORT`.
- O arquivo de log da API deve existir no host em `ALLOY_APP_LOG_PATH_HOST`.
- Para deploy seguro via proxy TLS, usar:
  - `ALLOY_TEMPO_OTLP_HTTP_ENDPOINT=https://usuario:senha@otlp-http.<dominio>`
  - `ALLOY_MIMIR_OTLP_HTTP_ENDPOINT=https://usuario:senha@mimir-otlp.<dominio>/otlp`
  - `ALLOY_LOKI_WRITE_URL=https://usuario:senha@loki-write.<dominio>/loki/api/v1/push`
- Em ambiente local com certificado self-signed, definir `ALLOY_EXPORT_TLS_INSECURE_SKIP_VERIFY=true`.
- Se surgir `connect: connection refused` para `localhost:9009`, significa que o Mimir nao esta neste host. Ajuste `ALLOY_MIMIR_OTLP_HTTP_ENDPOINT` para o host/domínio do servidor LGTM.
