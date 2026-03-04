# Prontuario API

Base inicial do projeto com FastAPI e Python 3.12.

## Requisitos
- Python 3.12+

## Execucao local
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d postgres
alembic upgrade head
uvicorn app.presentation.main:app --reload
```

## Banco de dados com Docker
```bash
docker compose up -d postgres
docker compose ps
docker compose down
```

## Healthcheck
- `GET /health`

## Medicos
- `POST /doctors`

## Autenticacao
- `POST /auth/login`

## Consultas
- `GET /patients/{id}/consultations`
- `POST /patients/{id}/consultations`

## Doencas
- `GET /diseases`
- `POST /diseases`

## Medicamentos
- `GET /medications`
- `POST /medications`

## Imagens
- `POST /images/presigned-url`
- `GET /patients/{id}/images`
- `POST /images/{id}/confirm-upload`

## Lesoes
- `POST /patients/{id}/lesions`
- `GET /patients/{id}/lesions`
- `PUT /lesions/{id}`

## Documentacao da API
- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- ReDoc: `GET /redoc`

## HTTPS obrigatorio em deploy
- Em staging/producao, configure no `.env`:
  - `ENFORCE_HTTPS=true`
  - `HSTS_ENABLED=true`
- Opcional para hardening HSTS:
  - `HSTS_MAX_AGE_SECONDS=31536000`
  - `HSTS_INCLUDE_SUBDOMAINS=true`
  - `HSTS_PRELOAD=true` (somente quando dominio estiver pronto para preload)

Observacao:
- Em deploy atras de load balancer/reverse proxy, encaminhe `X-Forwarded-Proto` corretamente para a API.

Validacao local ponta a ponta com TLS:
```bash
cp .env.example .env
./scripts/generate_local_tls_cert.sh
docker compose -f docker-compose.tls.yml up -d --build
```

Checks:
```bash
# 1) HTTP redireciona para HTTPS
curl -I http://localhost/health

# 2) HTTPS responde health
curl -k https://localhost/health

# 3) HSTS presente
curl -k -I https://localhost/health | grep -i strict-transport-security
```

Parar ambiente TLS:
```bash
docker compose -f docker-compose.tls.yml down
```

## Gestao de segredos (Secret Manager)
- Providers suportados:
  - `SECRET_PROVIDER=env` (desenvolvimento local)
  - `SECRET_PROVIDER=file` (arquivo JSON com segredos)
  - `SECRET_PROVIDER=aws_secrets_manager` (AWS Secrets Manager)
- Segredos gerenciados:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `JWT_SECRET_KEY`

Exemplo com provider por arquivo:
```bash
cp .secrets.example.json .secrets.json
```
E no `.env`:
```bash
SECRET_PROVIDER=file
SECRET_FILE_PATH=.secrets.json
```

Regras de deploy:
- Em `ENVIRONMENT=staging` ou `ENVIRONMENT=production`, o sistema bloqueia `SECRET_PROVIDER=env` por padrao.
- Use `SECRET_PROVIDER=file` ou `SECRET_PROVIDER=aws_secrets_manager`.
- Defina `ENCRYPTION_KEY` via secret manager para criptografia de campo.

## Classificacao de dados sensiveis
- Documento oficial: `ai_docs/data_classification.md`
- Registro técnico em código: `app/infrastructure/security/data_classification.py`

## Masking automatico de logs
- Logs estruturados com `structlog` foram integrados ao app.
- Campos `SENSITIVE` e `HIGHLY_SENSITIVE` sao mascarados automaticamente nos eventos de log.
- Middleware de request logging ativo para registrar metodo, rota, status, duracao e payload JSON (mascarado).

Configuracoes:
- `LOG_LEVEL=INFO`
- `LOG_JSON=false` (use `true` em ambientes com agregador de logs)
- `LOG_REQUEST_BODIES=true` (desative se quiser reduzir volume de logs)

## Rastreabilidade de requisicao (`request_id`)
- Cada requisicao recebe `request_id` (ou reaproveita `X-Request-ID` enviado pelo cliente).
- O valor é propagado em todos os logs estruturados da requisicao.
- A API devolve o header `X-Request-ID` na resposta.

## Criptografia de campo (HIGHLY_SENSITIVE)
- Campos protegidos no ORM:
  - `patient.notes`
  - `consultation.chief_complaint`
  - `consultation.physical_exam`
  - `consultation.conduct`
  - `audit_log.before_state`
  - `audit_log.after_state`
- A chave vem de `ENCRYPTION_KEY` (Fernet, base64 urlsafe 32 bytes).
- O ciphertext salvo no banco segue o formato `versao:token` (ex.: `v1:gAAAA...`).
- Chave ativa de escrita: `ENCRYPTION_ACTIVE_KEY_VERSION`.
- Conjunto de chaves legíveis: `ENCRYPTION_KEYS_JSON`.

Gerar chave nova:
```bash
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Exemplo de key ring:
```bash
ENCRYPTION_KEYS_JSON={"v1":"<key_v1>","v2":"<key_v2>"}
ENCRYPTION_ACTIVE_KEY_VERSION=v2
```

Fluxo de rotação (sem downtime):
1. Adicionar nova chave em `ENCRYPTION_KEYS_JSON` (mantendo antiga).
2. Trocar `ENCRYPTION_ACTIVE_KEY_VERSION` para a nova versão.
3. Recriptografar dados antigos em background.
4. Remover chave antiga apenas após concluir a migração.

Job de recriptografia por lote:
```bash
python scripts/reencrypt_fields.py --dry-run --batch-size 500
python scripts/reencrypt_fields.py --batch-size 500
```

Filtrar campos específicos:
```bash
python scripts/reencrypt_fields.py --dry-run --only patient.notes consultation.conduct
```

Automação no GitHub Actions:
- Workflow: `.github/workflows/rotate-encryption.yml`
- Execução manual (`workflow_dispatch`) com `dry_run` e `batch_size`
- Execução agendada semanal (segunda 04:00 UTC) em modo `dry-run`
- Secrets necessários no repositório:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `JWT_SECRET_KEY`
  - `ENCRYPTION_KEY`
  - `ENCRYPTION_KEYS_JSON`
  - `ENCRYPTION_ACTIVE_KEY_VERSION`

## Domain Event Bus
- Publicação de evento ocorre em todas as escritas via `AuditEventService`.
- Processamento de eventos pendentes (manual):
```bash
python scripts/process_domain_events.py --limit 100
```

## Observabilidade (LGTM)
- Stack base da Fase 1 em `deploy/observability`.
- Guia rápido: `deploy/observability/README.md`.

## Autenticacao (para endpoints protegidos)
- Use `Authorization: Bearer <token>`
- O token JWT deve conter `doctor_id` (ou `sub`) com UUID valido.
- Configure expiração com `JWT_ACCESS_TOKEN_EXP_MINUTES` (default: `60`).

Gerar token pela API:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"medico@exemplo.com","password":"senha-forte"}'
```

Exemplo rapido para gerar token local (com o mesmo `JWT_SECRET_KEY` do `.env`):
```bash
python3 -c 'import os, jwt; print(jwt.encode({"doctor_id":"7b1358ec-3b56-439a-a901-830f731ea64f"}, os.environ["JWT_SECRET_KEY"], algorithm="HS256"))'
```
