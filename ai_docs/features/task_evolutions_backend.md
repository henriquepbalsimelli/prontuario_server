# Task: Implementação da Entidade Evolution no Backend

## Objetivo

Implementar a entidade `Evolution` como registro clínico longitudinal de um
paciente, independente de consulta e com vínculo opcional a ela.

Uma evolução representa uma observação clínica realizada pelo médico em um
momento específico. Ela pode ser originada durante uma consulta ou em outros
contextos de acompanhamento.

## Dependência Obrigatória

Esta task só deve ser iniciada após a conclusão de
`task_audit_hardening.md`.

A criação e a atualização de evoluções devem utilizar o fluxo atômico e
sanitizado de auditoria definido nessa task.

## Modelo de Domínio

Criar a entidade `Evolution` com os seguintes campos:

| Campo | Tipo | Obrigatório | Regra |
| --- | --- | --- | --- |
| `id` | UUID | Sim | Identificador da evolução |
| `doctor_id` | UUID | Sim | Médico autenticado, tenant e autor interno |
| `patient_id` | UUID | Sim | Paciente ao qual a evolução pertence |
| `consultation_id` | UUID | Não | Consulta relacionada, quando aplicável |
| `origin_type` | Enum/string controlada | Sim | Origem clínica da evolução |
| `content` | Texto criptografado | Sim | Conteúdo clínico da evolução |
| `occurred_at` | Datetime com timezone | Sim | Momento clínico ao qual o registro se refere |
| `created_at` | Datetime com timezone | Sim | Momento da criação no sistema |
| `updated_at` | Datetime com timezone | Sim | Momento da última alteração |

### Origens Suportadas

O campo `origin_type` deve aceitar somente:

- `consultation`
- `inpatient_visit`
- `exam_review`
- `phone_contact`
- `telemedicine`
- `procedure`
- `hospital_event`
- `multidisciplinary_discussion`
- `other`

### Classificação de Dados

- `content`: `HIGHLY_SENSITIVE`, persistido com `EncryptedString`.
- `occurred_at` e `origin_type`: `SENSITIVE`.
- Identificadores e timestamps técnicos: `INTERNAL`.
- Atualizar o registro central de classificação e sua documentação.

## Persistência e Migração

- Criar tabela `evolution` em uma nova migration Alembic.
- Criar FK obrigatória para `doctor.id` com `ON DELETE CASCADE`.
- Criar FK obrigatória para `patient.id` com `ON DELETE CASCADE`.
- Criar FK opcional para `consultation.id` com `ON DELETE SET NULL`.
- Criar índice composto para listagem por
  `doctor_id`, `patient_id` e `occurred_at`.
- Criar índices para os vínculos necessários.
- Ordenar listagens por `occurred_at DESC` e usar `created_at DESC` como
  desempate.

## Regras de Negócio

- A evolução pertence diretamente ao paciente.
- Uma evolução pode existir sem consulta associada.
- Quando `consultation_id` for informado, a consulta deve pertencer ao mesmo
  `doctor_id` e `patient_id` da evolução.
- `content` deve ser normalizado e não pode estar vazio ou conter somente
  espaços.
- `origin_type` e `occurred_at` são obrigatórios na criação e atualização.
- Atualizações usam substituição completa dos campos clínicos via `PUT`.
- `id`, `doctor_id`, `patient_id` e `created_at` são preservados na
  atualização.
- Não disponibilizar exclusão de evoluções.
- Toda criação gera `EvolutionCreated`.
- Toda atualização gera `EvolutionUpdated`, com estados anterior e posterior no
  `audit_log`.
- `doctor_id` vem exclusivamente do contexto autenticado.

## Contrato da API

### Criar Evolução

`POST /patients/{patient_id}/evolutions`

Payload:

```json
{
  "consultation_id": "uuid opcional",
  "origin_type": "consultation",
  "content": "Conteúdo clínico da evolução",
  "occurred_at": "2026-06-04T14:30:00-03:00"
}
```

Resposta:

- `201 Created` com `EvolutionResponse`.
- `404 Not Found` quando o paciente ou a consulta associada não for acessível.
- `422 Unprocessable Entity` para payload inválido.

### Listar Evoluções do Paciente

`GET /patients/{patient_id}/evolutions?page=1&page_size=20`

Resposta:

- `200 OK` com lista paginada por parâmetros, ordenada por `occurred_at DESC`.
- `404 Not Found` quando o paciente não for acessível.

### Consultar Evolução

`GET /evolutions/{evolution_id}`

Resposta:

- `200 OK` com `EvolutionResponse`.
- `404 Not Found` quando a evolução não existir para o médico autenticado.

### Atualizar Evolução

`PUT /evolutions/{evolution_id}`

- Recebe todos os campos clínicos editáveis:
  `consultation_id`, `origin_type`, `content` e `occurred_at`.
- Retorna `200 OK` com `EvolutionResponse`.
- Retorna `404 Not Found` quando a evolução ou consulta associada não for
  acessível.
- Retorna `422 Unprocessable Entity` para payload inválido.

## Camadas a Implementar

- Modelo de domínio `Evolution`.
- Interface `EvolutionRepository`.
- Implementação `SQLAlchemyEvolutionRepository`.
- Métodos necessários no `ConsultationRepository` para validar o vínculo por
  médico e paciente.
- `EvolutionService` com listagem, detalhe, criação e atualização.
- Schemas de criação, atualização e resposta.
- Controller e registro do router.
- Dependency injection do service e repositories.
- Modelo SQLAlchemy e migration Alembic.
- Classificação de dados e documentação da API.

## Critérios de Aceite

- [ ] Evolução pode ser criada sem consulta associada.
- [ ] Evolução pode ser criada com consulta válida do mesmo médico e paciente.
- [ ] Consulta de outro médico ou paciente não pode ser associada.
- [ ] Todas as queries de evolução filtram por `doctor_id`.
- [ ] `content` vazio ou formado somente por espaços é rejeitado.
- [ ] `origin_type` aceita somente os valores controlados.
- [ ] `content` é armazenado criptografado.
- [ ] Listagem aplica paginação e ordenação por `occurred_at`.
- [ ] Detalhe de evolução respeita isolamento multi-tenant.
- [ ] Atualização preserva identidade, paciente, médico e data de criação.
- [ ] Criação e atualização geram auditoria e eventos de domínio.
- [ ] Eventos de domínio não expõem o conteúdo clínico.
- [ ] Não existe endpoint de exclusão.
- [ ] Migration executa upgrade e downgrade corretamente.
- [ ] `pytest -q` e `ruff check app alembic` passam sem erros.

## Testes Obrigatórios

- Testes unitários do service sem banco real.
- Testes de repository para filtros por `doctor_id` e `patient_id`.
- Testes de isolamento entre médicos.
- Testes de criação com e sem consulta.
- Testes de rejeição de consulta incompatível.
- Testes de validação de conteúdo e origem.
- Testes de ordenação e paginação.
- Testes de detalhe e atualização.
- Testes de auditoria atômica em criação e atualização.
- Testes do contrato OpenAPI para os quatro endpoints.

## Fora do Escopo

- Implementação na UI Flutter.
- Regeneração do cliente Dart.
- Filtros avançados por origem, consulta ou intervalo de datas.
- Exclusão de evoluções.
- Endpoint público de histórico de revisões.
- CRM, finalização ou assinatura digital.
- Autoria multiprofissional.
- Geração automática de evolução a partir de consulta.

## Definição de Concluído

A task estará concluída quando a entidade puder ser criada, listada, consultada
e atualizada pelo backend com isolamento multi-tenant, conteúdo criptografado,
vínculo opcional validado e auditoria atômica coberta por testes.
