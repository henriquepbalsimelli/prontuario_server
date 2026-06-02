# Observabilidade - Fase 2 (Segurança) Implementada

Data: 2026-03-04

## Entregas
- Reverse proxy Nginx com TLS e redirecionamento HTTP -> HTTPS.
- Proteção do Grafana com Basic Auth no proxy.
- Proteção de ingestão de telemetria com Basic Auth + allowlist por CIDR:
- Tempo OTLP HTTP
- Tempo OTLP gRPC
- Mimir OTLP HTTP
- Loki push API
- Rate limiting configurado para endpoints de Grafana e OTLP.
- Baseline de RBAC no Grafana (roles e hardening em configuração).

## Artefatos
- `deploy/observability/docker-compose.lgtm.secure.yml`
- `deploy/observability/proxy/templates/lgtm.conf.template`
- `deploy/observability/.env.secure.example`
- `deploy/observability/scripts/generate_basic_auth.sh`
- `deploy/observability/grafana/RBAC.md`

## Observações
- Certificados TLS devem ser fornecidos em `deploy/observability/proxy/certs/`.
- Arquivos `.htpasswd` devem ser gerados antes do deploy seguro.
- Em produção, usar senha forte e rotacionada para admin do Grafana.
- Quando possível, substituir Basic Auth de ingestão por mTLS/token gerenciado.
