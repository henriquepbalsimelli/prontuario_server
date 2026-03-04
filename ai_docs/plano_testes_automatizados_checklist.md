# Plano de Testes Automatizados - Checklist de Progresso

Referência principal: `ai_docs/principles.md` (SOLID, separação de camadas, DI obrigatória, teste sem banco real, `doctor_id` obrigatório e filtro por `doctor_id` em todas as queries).

## Objetivo
- Garantir qualidade funcional, arquitetural e de segurança do sistema.
- Reduzir regressões em fluxo clínico multi-tenant (isolamento por médico).
- Estabelecer esteira contínua de validação no CI.

## Status Geral
- Progresso total: `0%`
- Última atualização: `2026-02-27`
- Responsável: `time backend`

---

## Fase 1 - Fundação de testes (P0)
- [ ] Adicionar dependências: `pytest-asyncio`, `pytest-cov`, `pytest-mock`.
- [ ] Criar estrutura de testes:
  - [ ] `app/tests/unit`
  - [ ] `app/tests/integration`
  - [ ] `app/tests/contract`
  - [ ] `app/tests/fixtures`
- [ ] Criar `conftest.py` base com fixtures de UUID de médico, payloads e JWT.
- [ ] Configurar factories/fakes para `PatientRepository`.
- [ ] Definir comandos padrão:
  - [ ] `pytest -q app/tests/unit`
  - [ ] `pytest -q app/tests/integration`
  - [ ] `pytest -q --cov=app --cov-report=term-missing`

Critério de conclusão da Fase 1:
- [ ] Suíte executa localmente com sucesso e sem banco real para testes unitários.

---

## Fase 2 - Testes unitários de regra de negócio e segurança (P0)

### 2.1 Services (`app/application/services`)
- [ ] `PatientService.list_patients`: repassa paginação e `doctor_id` corretamente.
- [ ] `PatientService.get_patient`: retorna paciente quando existe.
- [ ] `PatientService.get_patient`: lança `PatientNotFoundError` quando inexistente.
- [ ] `PatientService.create_patient`: cria entidade com `id` novo e `doctor_id` do contexto.
- [ ] `PatientService.update_patient`: preserva `id`, `doctor_id` e `created_at`.
- [ ] `PatientService.update_patient`: lança `PatientNotFoundError` quando inexistente.
- [ ] `PatientService.delete_patient`: sucesso quando `repository.delete=True`.
- [ ] `PatientService.delete_patient`: lança `PatientNotFoundError` quando `False`.

### 2.2 Autenticação (`app/presentation/auth.py`)
- [ ] Aceita token válido com claim `doctor_id`.
- [ ] Aceita token válido com claim `sub`.
- [ ] Rejeita token inválido/assinatura incorreta (401).
- [ ] Rejeita token sem `doctor_id`/`sub` (401).
- [ ] Rejeita `doctor_id` malformado (401).

### 2.3 Configuração e segredos (`app/infrastructure/settings.py`, `app/infrastructure/secrets/providers.py`)
- [ ] `EnvSecretProvider` retorna valores esperados.
- [ ] `FileSecretProvider` carrega JSON válido.
- [ ] `FileSecretProvider` falha para arquivo ausente/inválido.
- [ ] Política de deploy bloqueia `SECRET_PROVIDER=env` em `staging/production`.
- [ ] `SECRET_PROVIDER=aws_secrets_manager` sem `AWS_SECRETS_ID` falha com erro explícito.

### 2.4 Middleware de segurança (`app/presentation/middlewares/security.py`)
- [ ] Redireciona para HTTPS quando `enforce_https=true` e request HTTP.
- [ ] Não redireciona quando request já é HTTPS.
- [ ] Aplica HSTS apenas quando `hsts_enabled=true` e request HTTPS.
- [ ] Não aplica HSTS em request HTTP.

Critério de conclusão da Fase 2:
- [ ] Cobertura unitária dos módulos existentes >= `85%`.

---

## Fase 3 - Testes de integração (P0/P1)

### 3.1 Repositório SQLAlchemy (`app/infrastructure/repositories/sqlalchemy_patient_repository.py`)
- [ ] `create` persiste registro corretamente.
- [ ] `get_by_id` retorna registro correto com filtro por `doctor_id`.
- [ ] `get_by_id` retorna `None` para paciente de outro médico.
- [ ] `list_by_doctor` aplica paginação (`page`, `page_size`) corretamente.
- [ ] `list_by_doctor` ordena por `created_at desc`.
- [ ] `update` atualiza campos permitidos e preserva identidade.
- [ ] `delete` retorna `True` quando remove e `False` quando não encontra.

### 3.2 API FastAPI (`app/presentation/controllers/patient_controller.py`)
- [ ] `GET /patients` retorna 200 com token válido.
- [ ] `POST /patients` retorna 201 e payload persistido.
- [ ] `GET /patients/{id}` retorna 404 para id inexistente.
- [ ] `PUT /patients/{id}` retorna 404 para id inexistente.
- [ ] `DELETE /patients/{id}` retorna 204 em sucesso.
- [ ] Endpoints protegidos retornam 401 sem token.
- [ ] Validação de payload inválido retorna 422.
- [ ] Isolamento multi-tenant: médico A não acessa dados do médico B.

Critério de conclusão da Fase 3:
- [ ] Integrações críticas de pacientes cobertas com banco de teste.

---

## Fase 4 - Contrato e arquitetura (P1)

### 4.1 Contrato de API
- [ ] Verificar presença de `GET /health` no OpenAPI.
- [ ] Verificar presença de CRUD de `/patients` no OpenAPI.
- [ ] Validar códigos de status principais por endpoint.

### 4.2 Regras arquiteturais do `principles.md`
- [ ] Controller não contém regra de negócio.
- [ ] Service não depende de FastAPI/HTTP.
- [ ] Repository não contém regra de domínio.
- [ ] Dependências injetadas via container/dependencies.
- [ ] Testes de service sem banco real.

Critério de conclusão da Fase 4:
- [ ] Regras arquiteturais críticas protegidas por testes automatizados.

---

## Fase 5 - CI/CD e qualidade contínua (P1)
- [ ] Criar workflow de CI com jobs separados:
  - [ ] `lint` (`ruff`)
  - [ ] `unit-tests`
  - [ ] `integration-tests` (com PostgreSQL de teste)
  - [ ] `coverage`
- [ ] Publicar relatório de cobertura no pipeline.
- [ ] Definir gate de cobertura inicial >= `70%`.
- [ ] Evoluir gate para >= `80%` após estabilização da suíte.
- [ ] Bloquear merge em falha de lint, testes ou cobertura.

Critério de conclusão da Fase 5:
- [ ] Pipeline verde e política de qualidade ativa para PR.

---

## Casos críticos obrigatórios (não negociáveis)
- [ ] Nenhuma query de paciente sem filtro por `doctor_id`.
- [ ] Nenhum endpoint de paciente acessível sem autenticação válida.
- [ ] Nenhum teste unitário de service dependente de banco real.
- [ ] Regressão de isolamento entre médicos detectável por teste automático.

---

## Backlog de expansão (quando novos módulos entrarem)
- [ ] Consultas (`consultation`) com isolamento por `doctor_id`.
- [ ] Imagens clínicas (`image`) com autorização por médico/paciente.
- [ ] Lesões (`lesion`) com histórico e validações clínicas.
- [ ] Eventos de domínio em toda escrita (ex.: `PatientCreated`, `PatientUpdated`).
- [ ] Auditoria obrigatória em toda escrita (`audit_log` completo).

---

## Registro de progresso (preencher ao longo da execução)

### Sprint atual
- Meta:
- Itens concluídos:
- Bloqueios:
- Próximos passos:

### Histórico de atualizações
- `2026-02-27`: checklist inicial criado.
