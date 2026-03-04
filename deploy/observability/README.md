# LGTM Stack (Servidor de Observabilidade)

Este diretório contém a base da Fase 1 para provisionar Grafana, Loki, Tempo e Mimir com persistência local.

## Subir stack
```bash
cd deploy/observability
cp .env.example .env
docker compose -f docker-compose.lgtm.yml up -d
```

## Verificar status
```bash
docker compose -f docker-compose.lgtm.yml ps
```

## Endpoints locais
- Grafana: `http://localhost:3000`
- Loki: `http://localhost:3100`
- Tempo: `http://localhost:3200`
- Mimir: `http://localhost:9009`

## Persistência (volumes)
- `grafana_data`
- `loki_data`
- `tempo_data`
- `mimir_data`

## Provisionamento automático no Grafana
- Datasources criadas automaticamente:
  - Loki (`http://loki:3100`)
  - Tempo (`http://tempo:3200`)
  - Mimir (`http://mimir:9009/prometheus`)

## Retenção aplicada (baseline)
- Loki: `30d` (em `loki-config.yml`)
- Tempo: `14d` (336h em `tempo.yml`)
- Mimir: `30d` (em `mimir.yml`)

## Variáveis úteis
- `GRAFANA_ADMIN_USER` (default: `admin`)
- `GRAFANA_ADMIN_PASSWORD` (default: `admin`)
- `GRAFANA_ROOT_URL` (default: `http://localhost:3000`)

## Observação de segurança
- Esta Fase 1 sobe os serviços e persistência.
- TLS, autenticação de ingestão e hardening do acesso público serão tratados na Fase 2.

## Fase 2 (modo seguro para deploy)
Arquivos:
- `docker-compose.lgtm.secure.yml`
- `proxy/templates/lgtm.conf.template`
- `scripts/generate_basic_auth.sh`
- `.env.secure.example`

Passos:
```bash
cd deploy/observability
cp .env.secure.example .env

# gerar basic auth para Grafana e OTLP
./scripts/generate_basic_auth.sh grafana_user 'senha-forte-grafana' otlp_user 'senha-forte-otlp'

# adicionar certificados TLS
# proxy/certs/fullchain.pem
# proxy/certs/privkey.pem

docker compose -f docker-compose.lgtm.secure.yml up -d
```

Comportamento do proxy:
- Redireciona `HTTP -> HTTPS`.
- Exige Basic Auth para `grafana.<dominio>`.
- Exige Basic Auth + allowlist de IP/CIDR para `otlp-http.<dominio>` e `otlp-grpc.<dominio>`.
- Aplica rate limiting nos endpoints públicos/ingestão.
