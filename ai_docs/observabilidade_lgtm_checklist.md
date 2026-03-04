# Checklist de Implementação - Observabilidade (LGTM + OpenTelemetry)

## Escopo de infraestrutura (2 servidores)
- [ ] Confirmar arquitetura final: 1 servidor API + 1 servidor LGTM
- [ ] Definir DNS/TLS para acesso ao Grafana e endpoints de ingestão
- [ ] Definir portas, firewall e regras de rede entre API <-> LGTM

## Fase 0 - Requisitos e SLOs
- [ ] Definir SLO de disponibilidade da API
- [ ] Definir SLO de latência (p95/p99)
- [ ] Definir SLO de erro (4xx/5xx relevantes)
- [ ] Definir retenção para logs, traces e métricas
- [ ] Definir limites de cardinalidade (labels/attributes)

## Fase 1 - Provisionar servidor LGTM
- [ ] Subir Grafana com volume persistente
- [ ] Subir Loki com volume persistente
- [ ] Subir Tempo com volume persistente
- [ ] Subir Mimir com volume persistente
- [ ] Configurar datasource Loki no Grafana
- [ ] Configurar datasource Tempo no Grafana
- [ ] Configurar datasource Mimir (Prometheus) no Grafana
- [ ] Configurar retenção do Loki (compactor + retention)
- [ ] Configurar retenção do Tempo
- [ ] Configurar retenção do Mimir

## Fase 2 - Segurança no servidor LGTM
- [ ] Configurar reverse proxy (Nginx/Traefik) com TLS
- [ ] Proteger Grafana com autenticação forte
- [ ] Proteger endpoints de ingestão OTLP com autenticação
- [ ] Aplicar rate limiting nos endpoints públicos
- [ ] Restringir acesso por IP (quando possível)
- [ ] Configurar RBAC no Grafana

## Fase 3 - Collector/Agent no servidor API
- [ ] Instalar Grafana Alloy no servidor da API
- [ ] Configurar receiver OTLP (gRPC/HTTP) no Alloy
- [ ] Configurar pipeline de traces -> Tempo
- [ ] Configurar pipeline de métricas -> Mimir
- [ ] Configurar pipeline de logs -> Loki
- [ ] Habilitar `batch`, `memory_limiter`, retry e queue nos exporters
- [ ] Validar envio com teste de conectividade ponta a ponta

## Fase 4 - Instrumentação da API FastAPI
- [ ] Adicionar dependências OpenTelemetry no projeto
- [ ] Instrumentar FastAPI (request lifecycle)
- [ ] Instrumentar cliente HTTP (saídas para serviços externos)
- [ ] Instrumentar SQLAlchemy (queries e tempo de banco)
- [ ] Configurar `service.name`, `service.version`, `deployment.environment`
- [ ] Excluir endpoints de ruído (`/health`, `/docs`, `/openapi.json`)
- [ ] Propagar `trace_id`/`span_id` nos logs estruturados
- [ ] Manter correlação com `request_id` já existente

## Fase 5 - Dashboards e Alertas
- [ ] Criar dashboard RED (Rate, Errors, Duration)
- [ ] Criar dashboard de infraestrutura da API (CPU, memória, restart)
- [ ] Criar dashboard de logs por status, rota e `request_id`
- [ ] Criar visão de traces com busca por `trace_id`
- [ ] Criar alertas de erro 5xx acima do limiar
- [ ] Criar alertas de latência p95/p99 acima do limiar
- [ ] Criar alertas de indisponibilidade de ingestão no Alloy
- [ ] Criar alertas de uso de disco alto no servidor LGTM

## Fase 6 - Segurança de dados e compliance
- [ ] Revisar masking de dados sensíveis nos logs enviados ao Loki
- [ ] Garantir que dados HIGHLY_SENSITIVE não sejam atributos de span
- [ ] Revisar labels de métricas para evitar dados sensíveis
- [ ] Documentar política de retenção por classificação de dados
- [ ] Revisar trilha de auditoria para acessos ao Grafana

## Fase 7 - Operação e confiabilidade
- [ ] Criar runbook para "sem dados no Grafana"
- [ ] Criar runbook para "falha de ingestão OTLP"
- [ ] Criar runbook para "alta cardinalidade"
- [ ] Definir rotina de backup de configurações e dashboards
- [ ] Definir rotina de atualização de versões LGTM
- [ ] Executar teste de resiliência (indisponibilidade temporária do LGTM)

## Critérios de aceite (Go-live)
- [ ] API gera traces e aparecem no Tempo
- [ ] API gera métricas e aparecem no Mimir/Grafana
- [ ] Logs da API chegam no Loki com `request_id` e `trace_id`
- [ ] Dashboards principais publicados e revisados
- [ ] Alertas principais disparados e validados em teste controlado
- [ ] Segurança de acesso e retenção aprovadas
- [ ] Documentação operacional finalizada
