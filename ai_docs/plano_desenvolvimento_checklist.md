# Plano de Desenvolvimento - Checklist de Progresso

## 1. Fundação e segurança base
- [x] Inicialização da API com FastAPI + Python 3.12
- [x] Estrutura de camadas criada (`domain`, `application`, `infrastructure`, `presentation`)
- [x] DI inicial implementada (`Container`, dependencies)
- [x] Documentação Swagger/OpenAPI habilitada
- [x] Configuração de ambiente via `Settings` (`.env`)
- [x] HTTPS obrigatório configurado para todos ambientes de deploy
- [x] Gestão formal de segredos (vault/KMS/secret manager)

## 2. Estratégia de criptografia (crítico)
- [x] Classificação de dados sensíveis formalizada
- [ ] Criptografia em trânsito (TLS) validada ponta a ponta
- [ ] Criptografia em repouso definida e aplicada (DB, Redis, S3, backups)
- [x] Criptografia de campo para dados clínicos sensíveis
- [x] Estratégia de chaves (KEK/DEK), versão e rotação implementada
- [ ] Política de algoritmos aprovada (AES-256-GCM, Argon2/bcrypt)

## 3. Modelagem e banco com segurança
- [x] SQLAlchemy async configurado
- [x] Alembic configurado
- [x] Migration inicial criada
- [x] Índices obrigatórios principais adicionados (`doctor_id`, compostos com `created_at`)
- [ ] Modelagem específica para criptografia por campo (metadados de chave/nonce)
- [ ] Regras de imutabilidade de `audit_log` reforçadas no banco (guards/triggers/políticas)

## 4. Aplicação e domínio
- [x] Fluxo de `patients` implementado (service/repository/controller/schemas)
- [x] Isolamento por `doctor_id` aplicado no repositório de pacientes
- [x] JWT com extração de `doctor_id` no contexto autenticado
- [ ] Demais casos de uso (consultations, diseases, medications, images, lesions)
- [ ] Camada de criptografia integrada aos services

## 5. Infraestrutura segura
- [x] Docker Compose do PostgreSQL com volume persistente
- [ ] Redis integrado
- [ ] S3 adapter com bucket privado, versionamento e presigned URL
- [ ] Hardening de banco (TLS em conexão, backup criptografado)
- [ ] Hardening de Redis (TLS/segurança de acesso)

## 6. Auditoria e eventos
- [x] Tabelas `audit_log` e `domain_event` criadas no schema
- [x] EventBus implementado
- [x] Geração de evento em toda operação de escrita
- [x] Registro de auditoria em toda operação de escrita
- [ ] Proteção contra exposição de dados sensíveis em auditoria

## 7. API e endpoints
- [x] Endpoints de healthcheck
- [x] Endpoints de pacientes (CRUD)
- [x] Endpoints de consultas
- [x] Endpoints de doenças
- [x] Endpoints de medicamentos
- [x] Endpoints de imagens (presigned URL + listagem)
- [x] Endpoints de lesões

## 8. Testes e qualidade
- [ ] Testes unitários de services
- [ ] Testes unitários de EventBus
- [ ] Testes de autorização por `doctor_id`
- [ ] Testes de isolamento entre médicos
- [ ] Testes de integração de repositories
- [ ] Testes de integração de persistência de eventos/auditoria
- [ ] Cobertura mínima de 80% no CI

## 9. Observabilidade e operação
- [x] `structlog` integrado
- [ ] OpenTelemetry integrado
- [ ] CI/CD com GitHub Actions completo (lint, test, coverage, migrations)
- [x] Políticas de log com mascaramento de dados sensíveis
- [x] `request_id` propagado em logs e resposta (`X-Request-ID`)

---

## Resumo rápido
- Itens concluídos: base de projeto, banco/migrations, Swagger, autenticação JWT básica e CRUD de pacientes.
- Itens críticos pendentes: criptografia (estratégia + implementação), auditoria/eventos funcionais, demais módulos clínicos e suíte de testes.

