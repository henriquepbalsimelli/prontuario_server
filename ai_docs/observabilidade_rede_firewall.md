# Observabilidade - Rede, Portas e Firewall

Data de definição: 2026-03-04

## Escopo
Definir tráfego permitido entre os dois servidores do ambiente de produção:
- `api-server` (FastAPI + Alloy)
- `observability-server` (Grafana + Loki + Tempo + Mimir + reverse proxy)

## Princípios
- Deny-all por padrão (entrada e saída).
- Liberar apenas portas estritamente necessárias.
- Tráfego de ingestão sempre via TLS.
- Serviços internos LGTM não expostos publicamente.

## Matriz de portas (produção)

| Origem | Destino | Porta | Protocolo | TLS | Finalidade | Exposição |
|---|---|---:|---|---|---|---|
| Internet (IPs autorizados) | observability-server | 443 | TCP/HTTPS | Sim | Acesso ao Grafana (`grafana.<dominio>`) | Pública com controle |
| api-server | observability-server | 443 | TCP/HTTPS | Sim | Ingestão OTLP HTTP (`otlp-http.<dominio>`) | Privada/restrita |
| api-server | observability-server | 443 | TCP/HTTPS (h2) | Sim | Ingestão OTLP gRPC (`otlp-grpc.<dominio>`) | Privada/restrita |
| observability-server | Internet (ACME) | 80/443 | TCP | Sim (443) | Emissão/renovação de certificado | Saída |
| api-server | Internet (opcional) | 53/123/443 | UDP/TCP | N/A | DNS/NTP/updates | Saída controlada |

## Portas internas no observability-server (não expor publicamente)
- Grafana interno: `3000`
- Loki interno: `3100`
- Tempo interno (OTLP gRPC): `4317`
- Tempo interno (OTLP HTTP): `4318`
- Mimir interno: `9009` (varia por deploy)

Observação:
- O reverse proxy encerra TLS em `443` e roteia internamente para os serviços.
- O firewall deve bloquear acesso externo direto às portas internas acima.

## Regras mínimas de firewall
- `observability-server` inbound:
- permitir `443/tcp` de IPs administrativos para Grafana
- permitir `443/tcp` de `api-server` para ingestão OTLP
- negar `0.0.0.0/0` para `3000,3100,4317,4318,9009`
- `api-server` outbound:
- permitir `443/tcp` para `observability-server`
- negar tráfego para destinos/portas não necessários

## Regras recomendadas adicionais
- Criar allowlist separada para acesso humano ao Grafana.
- Usar rede privada (VPC/VPN/peering) para tráfego API -> observabilidade.
- Habilitar logs de firewall e retenção mínima para auditoria.
- Habilitar rate limiting no proxy para endpoints de ingestão.

## Critérios de aceite deste tópico
- Matriz de portas aprovada.
- Regras de firewall aplicadas em ambos os servidores.
- Sem exposição pública das portas internas do LGTM.
- API consegue enviar telemetria via `443` com TLS para o servidor LGTM.
