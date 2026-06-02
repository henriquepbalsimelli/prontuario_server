# Observabilidade - Fase 5 (Dashboards e Alertas)

Data: 2026-03-05

## Entregas
- Dashboard RED (Rate, Errors, Duration).
- Dashboard de infraestrutura da API (CPU, memória, restart e up do Alloy).
- Dashboard de logs com filtro por `request_id`.
- Dashboard para fluxo de troubleshooting de traces por `trace_id`.
- Regras de alerta provisionadas para:
  - erro 5xx acima do limiar
  - latência p95 acima do limiar
  - indisponibilidade de ingestão no Alloy
  - uso de disco alto no servidor LGTM

## Artefatos
- `deploy/observability/grafana/provisioning/dashboards/dashboard-api-red.json`
- `deploy/observability/grafana/provisioning/dashboards/dashboard-api-infra.json`
- `deploy/observability/grafana/provisioning/dashboards/dashboard-api-logs.json`
- `deploy/observability/grafana/provisioning/dashboards/dashboard-api-traces.json`
- `deploy/observability/grafana/provisioning/alerting/alerts.yml`

## Observações
- As queries seguem os nomes de métricas usados na instrumentação OTel implementada na Fase 4.
- Alguns painéis/alertas de infraestrutura dependem de métricas adicionais (ex.: `node_filesystem_*`, `kube_pod_container_status_restarts_total`) quando disponíveis no ambiente.
- Dashboards são provisionados automaticamente via `dashboard-providers.yml`.
