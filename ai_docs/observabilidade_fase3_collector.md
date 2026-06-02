# Observabilidade - Fase 3 (Collector/Agent API)

Data: 2026-03-04

## Entregas
- Alloy preparado para rodar no servidor da API.
- Receiver OTLP local (`4317` gRPC / `4318` HTTP).
- Pipeline de traces -> Tempo (OTLP HTTP).
- Pipeline de métricas -> Mimir (OTLP HTTP).
- Pipeline de logs de arquivo -> Loki.
- Processamento resiliente com `memory_limiter`, `batch`, `retry_on_failure` e `sending_queue` nos exporters OTel.

## Artefatos
- `deploy/api_observability/alloy/config.alloy`
- `deploy/api_observability/docker-compose.alloy.yml`
- `deploy/api_observability/.env.alloy.example`
- `deploy/api_observability/scripts/test_connectivity.sh`
- `deploy/api_observability/README.md`

## Validação executada
- Compose do Alloy validado com `docker compose config`.
- Container Alloy iniciado com sucesso e receiver OTLP ativo em `4317` e `4318`.
- Script de conectividade executado com sucesso (portas locais + reachability de Loki/Mimir/Tempo).

## Observações
- O endpoint de métricas foi definido em OTLP HTTP (`.../otlp`) para alinhamento com o pipeline único OTel.
- Para ambiente local de teste, foi usado mapeamento de portas do Alloy em `14317`/`14318` para evitar conflito com a stack LGTM local.
- A instrumentação da aplicação FastAPI (envio real de traces/métricas) ocorre na Fase 4.
