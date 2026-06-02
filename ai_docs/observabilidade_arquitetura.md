# Observabilidade - Arquitetura de Deploy (Confirmada)

Data de confirmação: 2026-03-04

## Topologia
- Servidor 1 (`api-server`): hospeda a aplicação FastAPI e o agente/collector (Grafana Alloy).
- Servidor 2 (`observability-server`): hospeda stack LGTM (Grafana, Loki, Tempo, Mimir).

## Objetivo da separação
- Isolar carga operacional da observabilidade do servidor transacional da API.
- Permitir escalar observabilidade e API de forma independente.
- Reduzir impacto de incidentes de monitoramento na disponibilidade da API.

## Fluxo de dados
1. A API gera telemetria via OpenTelemetry SDK (traces + métricas).
2. A API envia OTLP para o Alloy local no `api-server`.
3. O Alloy exporta:
- traces para Tempo (`observability-server`)
- métricas para Mimir (`observability-server`)
- logs para Loki (`observability-server`)
4. O Grafana consulta Loki/Tempo/Mimir para dashboards e troubleshooting.

No deploy seguro, toda a ingestão entre `api-server` e `observability-server` ocorre via reverse proxy TLS em `443`, com domínios dedicados por tipo de telemetria. As portas internas `3100`, `4317`, `4318` e `9009` permanecem privadas.

## Fronteiras de responsabilidade
- `api-server`
- aplicação FastAPI
- configuração de instrumentação OpenTelemetry
- execução e saúde do Alloy
- `observability-server`
- disponibilidade dos serviços LGTM
- retenção/persistência de dados de observabilidade
- autenticação/autorização de acesso ao Grafana e endpoints de ingestão

## Premissas aprovadas
- Não haverá co-location da stack LGTM junto da API no mesmo servidor em produção.
- Comunicação entre os servidores ocorrerá por rede privada/VPN ou regras de firewall estritas.
- Endpoints públicos de observabilidade devem estar protegidos com TLS e autenticação.

## Próximos itens do checklist
- Revisar masking de dados sensíveis nos logs enviados ao Loki.
- Garantir que dados HIGHLY_SENSITIVE não sejam atributos de span.
- Revisar labels de métricas para evitar dados sensíveis.
