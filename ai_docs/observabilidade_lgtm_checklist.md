# Checklist de Implementação - Observabilidade (LGTM + OpenTelemetry)

## Escopo de infraestrutura (2 servidores)
- [x] Confirmar arquitetura final: 1 servidor API + 1 servidor LGTM
- [x] Definir DNS/TLS para acesso ao Grafana e endpoints de ingestão
- [x] Definir portas, firewall e regras de rede entre API <-> LGTM

## Fase 0 - Requisitos e SLOs
- [x] Definir SLO de disponibilidade da API
- [x] Definir SLO de latência (p95/p99)
- [x] Definir SLO de erro (4xx/5xx relevantes)
- [x] Definir retenção para logs, traces e métricas
- [x] Definir limites de cardinalidade (labels/attributes)

## Fase 1 - Provisionar servidor LGTM
- [x] Subir Grafana com volume persistente
- [x] Subir Loki com volume persistente
- [x] Subir Tempo com volume persistente
- [x] Subir Mimir com volume persistente
- [x] Configurar datasource Loki no Grafana
- [x] Configurar datasource Tempo no Grafana
- [x] Configurar datasource Mimir (Prometheus) no Grafana
- [x] Configurar retenção do Loki (compactor + retention)
- [x] Configurar retenção do Tempo
- [x] Configurar retenção do Mimir

## Fase 2 - Segurança no servidor LGTM
- [x] Configurar reverse proxy (Nginx/Traefik) com TLS
- [x] Proteger Grafana com autenticação forte
- [x] Proteger endpoints de ingestão OTLP com autenticação
- [x] Aplicar rate limiting nos endpoints públicos
- [x] Restringir acesso por IP (quando possível)
- [x] Configurar RBAC no Grafana

## Fase 3 - Collector/Agent no servidor API
- [x] Instalar Grafana Alloy no servidor da API
- [x] Configurar receiver OTLP (gRPC/HTTP) no Alloy
- [x] Configurar pipeline de traces -> Tempo
- [x] Configurar pipeline de métricas -> Mimir
- [x] Configurar pipeline de logs -> Loki
- [x] Habilitar `batch`, `memory_limiter`, retry e queue nos exporters
- [x] Validar envio com teste de conectividade ponta a ponta

## Fase 4 - Instrumentação da API FastAPI
- [x] Adicionar dependências OpenTelemetry no projeto
- [x] Instrumentar FastAPI (request lifecycle)
- [x] Instrumentar cliente HTTP (saídas para serviços externos)
- [x] Instrumentar SQLAlchemy (queries e tempo de banco)
- [x] Configurar `service.name`, `service.version`, `deployment.environment`
- [x] Excluir endpoints de ruído (`/health`, `/docs`, `/openapi.json`)
- [x] Propagar `trace_id`/`span_id` nos logs estruturados
- [x] Manter correlação com `request_id` já existente

## Fase 5 - Dashboards e Alertas
- [x] Criar dashboard RED (Rate, Errors, Duration)
- [x] Criar dashboard de infraestrutura da API (CPU, memória, restart)
- [x] Criar dashboard de logs por status, rota e `request_id`
- [x] Criar visão de traces com busca por `trace_id`
- [x] Criar alertas de erro 5xx acima do limiar
- [x] Criar alertas de latência p95/p99 acima do limiar
- [x] Criar alertas de indisponibilidade de ingestão no Alloy
- [x] Criar alertas de uso de disco alto no servidor LGTM

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
