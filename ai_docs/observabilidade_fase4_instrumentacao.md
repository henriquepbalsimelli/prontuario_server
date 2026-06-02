# Observabilidade - Fase 4 (Instrumentação FastAPI)

Data: 2026-03-04

## Entregas
- Dependências OpenTelemetry adicionadas ao projeto Python.
- Instrumentação da aplicação FastAPI no bootstrap.
- Instrumentação de cliente HTTP (`httpx`).
- Instrumentação de SQLAlchemy (engine async via `sync_engine`).
- Configuração de atributos de recurso:
  - `service.name`
  - `service.version`
  - `deployment.environment`
- Exclusão de endpoints de ruído (`/health`, `/docs`, `/openapi.json`, `/redoc`).
- Correlação de logs com `trace_id` e `span_id` no `structlog`.
- Correlação existente com `request_id` preservada.

## Artefatos
- `app/infrastructure/observability/otel.py`
- `app/infrastructure/observability/__init__.py`
- `app/presentation/main.py`
- `app/infrastructure/settings.py`
- `app/infrastructure/logging/config.py`
- `pyproject.toml`
- `.env.example`

## Observações
- A inicialização OTel é controlada por `OTEL_ENABLED`.
- Se dependências OTel não estiverem instaladas, o app registra erro e segue sem instrumentação.
- Exportação padrão usa OTLP gRPC (`OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:14317`).
- Em produção com Alloy no mesmo host da API, manter endpoint OTLP local.
