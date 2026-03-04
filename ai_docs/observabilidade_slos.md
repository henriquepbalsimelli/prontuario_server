# Observabilidade - SLOs e Políticas Iniciais

Data de definição inicial: 2026-03-04

## Escopo
SLOs e políticas operacionais para a API em produção, medidos com telemetria OpenTelemetry/Alloy e armazenados no LGTM.

## SLO 1 - Disponibilidade da API

### Objetivo
- Disponibilidade mensal >= **99.5%**.

### SLI
- **requisições válidas com status < 500 / total de requisições válidas**

Definições:
- Requisições válidas: endpoints de negócio (exclui `health`, `docs`, `openapi`, `redoc`).
- Falha de disponibilidade: respostas `5xx` e timeout da API.

### Janela
- Rolling de 30 dias.

### Error Budget
- 0.5% de requisições válidas por mês.

### Alertas recomendados
- Taxa de `5xx` > 2% por 5 minutos.
- Disponibilidade < 99.5% em janela de 1 hora.

## SLO 2 - Latência da API (p95/p99)

### Objetivo
- p95 de latência <= **300 ms** (mensal).
- p99 de latência <= **800 ms** (mensal).

### SLI
- Quantis p95/p99 da duração de requisições HTTP da API, por rota de negócio.

Definições:
- Mesma exclusão de endpoints não críticos (`health`, `docs`, `openapi`, `redoc`).
- Métrica base: duração total de request no servidor da API.

### Janela
- Rolling de 30 dias para conformidade.
- Janelas operacionais de 5 minutos e 1 hora para alertas.

### Alertas recomendados
- p95 > 500 ms por 10 minutos.
- p99 > 1.2 s por 10 minutos.

## SLO 3 - Taxa de erro (4xx/5xx)

### Objetivo
- Taxa de `5xx` mensal <= **1.0%**.
- Taxa de `4xx` monitorada separadamente (não conta como indisponibilidade), alvo <= **5.0%**.

### SLI
- `5xx_rate = respostas_5xx / total_respostas_validas`
- `4xx_rate = respostas_4xx / total_respostas_validas`

Definições:
- `5xx` indica erro do serviço (confiabilidade da API).
- `4xx` indica erro de cliente/uso; trataremos como indicador de qualidade de contrato/documentação.

### Janela
- Rolling de 30 dias.

### Alertas recomendados
- `5xx_rate > 2%` por 5 minutos (página).
- `4xx_rate > 10%` por 15 minutos (warning).

## Política de retenção (logs, traces, métricas)

### Objetivos
- Garantir capacidade de troubleshooting recente.
- Controlar custo de armazenamento.
- Atender requisitos de compliance sem retenção excessiva.

### Retenção inicial recomendada
- Logs (Loki): **30 dias**.
- Traces (Tempo): **14 dias**.
- Métricas (Mimir):
- resolução bruta: **30 dias**
- dados agregados/downsampled (quando aplicável): **90 dias**

### Revisão
- Revisar retenção a cada 30 dias nos primeiros 3 meses de operação.

## Política de cardinalidade (labels/attributes)

### Regras obrigatórias
- Não usar valores de alta variabilidade como label/attribute indexável:
- `request_id`, `trace_id`, `patient_id`, `doctor_id`, emails, UUIDs arbitrários, mensagens de erro completas.
- Labels permitidas em métricas:
- `service.name`, `deployment.environment`, `http.method`, `http.route`, `http.status_code` (com controle), `error.type` (normalizado).
- Em logs e spans, IDs podem existir no payload, mas não como labels de agregação no backend.

### Limites práticos iniciais
- Máximo de combinações ativas por métrica crítica: **<= 1.000** por serviço.
- Máximo de atributos customizados por span: **<= 20**.
- Máximo de labels customizadas por stream de logs: **<= 10**.

### Controle operacional
- Revisão semanal de métricas com maior cardinalidade.
- Bloqueio de deploy para mudanças que aumentem cardinalidade sem revisão.

## Governança e evolução
- Este baseline pode ser endurecido após 2-3 ciclos mensais estáveis.
- Alterações em SLO/retenção/cardinalidade exigem registro em `ai_docs` com data e justificativa.
