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
- Instalar Grafana Alloy no servidor da API.
- Configurar receiver OTLP (gRPC/HTTP) no Alloy.
- Configurar pipeline de traces -> Tempo.
- Configurar pipeline de métricas -> Mimir.
- Configurar pipeline de logs -> Loki.
