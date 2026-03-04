# Observabilidade - Padrão DNS/TLS

Data de definição: 2026-03-04

## Objetivo
Definir padrão único de DNS e TLS para acesso ao Grafana e ingestão de telemetria no ambiente com 2 servidores (`api-server` e `observability-server`).

## Convenção de domínios
- Grafana (UI): `grafana.<seu-dominio>`
- OTLP gRPC (collector ingress): `otlp-grpc.<seu-dominio>`
- OTLP HTTP (collector ingress): `otlp-http.<seu-dominio>`

Observação:
- Loki/Tempo/Mimir não devem ser expostos diretamente em domínio público.
- O acesso externo passa pelo reverse proxy no `observability-server`.

## TLS (obrigatório)
- Todos os domínios acima devem operar apenas em HTTPS/TLS.
- Certificados recomendados: Let's Encrypt (produção) ou AC interno (ambientes fechados).
- Política mínima:
- TLS 1.2+ (preferir TLS 1.3 quando disponível)
- Redirecionamento HTTP -> HTTPS
- Renovação automática de certificado

## Modelo de exposição
- Público (com autenticação):
- `grafana.<seu-dominio>`
- Privado/restrito (ingestão de telemetria):
- `otlp-grpc.<seu-dominio>`
- `otlp-http.<seu-dominio>`

## Regras de segurança associadas
- Exigir autenticação na ingestão OTLP (header/token ou mTLS, conforme política).
- Permitir ingestão OTLP apenas da origem do `api-server`.
- Aplicar rate limiting no reverse proxy para endpoints de ingestão.
- Habilitar logs de acesso no proxy para auditoria.

## Resolução DNS
- Todos os nomes devem resolver para o IP público/privado do `observability-server` (conforme arquitetura de rede).
- Em produção, preferir resolução privada entre servidores quando houver VPN/VPC.

## Critérios de aceite deste tópico
- DNS de Grafana definido.
- DNS de OTLP gRPC definido.
- DNS de OTLP HTTP definido.
- Certificados TLS emitidos e válidos para todos os hosts.
- HTTP bloqueado/redirecionado para HTTPS.
