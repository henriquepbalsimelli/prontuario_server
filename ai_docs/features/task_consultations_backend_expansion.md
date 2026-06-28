# Task: Expansão do Backend de Consultas

## Objetivo

Expandir o contrato de `Consultation` para suportar uma área própria de
consultas no prontuário, separada da área de evoluções clínicas.

Uma consulta representa o atendimento médico realizado com o paciente. Uma
evolução representa um registro clínico longitudinal e pode ou não estar
vinculada a uma consulta.

Esta task complementa os endpoints existentes de criação e listagem de
consultas com detalhe, atualização e listagem das evoluções vinculadas.

## Dependências Obrigatórias

- A atualização de consultas deve utilizar o fluxo atômico e sanitizado de
  auditoria definido em `task_audit_hardening.md`.
- O endpoint de evoluções vinculadas só deve ser implementado após a conclusão
  de `task_evolutions_backend.md`.

## Regras de Negócio

- Consulta e evolução são entidades distintas.
- Uma consulta pertence diretamente a um médico e a um paciente.
- Todas as operações devem filtrar pelo `doctor_id` autenticado.
- O detalhe e a atualização devem retornar `404 Not Found` quando a consulta
  não existir ou não pertencer ao médico autenticado.
- Atualizações usam substituição completa dos campos clínicos via `PUT`.
- `id`, `doctor_id`, `patient_id` e `created_at` são preservados na atualização.
- Não disponibilizar exclusão de consultas nesta task.
- A atualização deve gerar auditoria atômica com estados anterior e posterior.
- A listagem de evoluções vinculadas deve retornar somente evoluções da
  consulta informada e respeitar o mesmo médico e paciente.
- Criar uma evolução vinculada continua sendo responsabilidade de
  `POST /patients/{patient_id}/evolutions`, com `consultation_id` no payload.

## Contrato da API

### Consultar Consulta

`GET /consultations/{consultation_id}`

Resposta:

- `200 OK` com `ConsultationResponse`.
- `404 Not Found` quando a consulta não existir para o médico autenticado.

### Atualizar Consulta

`PUT /consultations/{consultation_id}`

Payload:

```json
{
  "consultation_date": "2026-06-04",
  "chief_complaint": "Queixa principal",
  "physical_exam": "Descrição do exame físico",
  "conduct": "Conduta adotada"
}
```

Resposta:

- `200 OK` com `ConsultationResponse`.
- `404 Not Found` quando a consulta não existir para o médico autenticado.
- `422 Unprocessable Entity` para payload inválido.

### Listar Evoluções Vinculadas

`GET /consultations/{consultation_id}/evolutions?page=1&page_size=20`

Resposta:

- `200 OK` com lista de `EvolutionResponse`, ordenada por
  `occurred_at DESC` e `created_at DESC`.
- `404 Not Found` quando a consulta não existir para o médico autenticado.

## Camadas a Implementar

- Método de detalhe no `ConsultationRepository`.
- Método de atualização no `ConsultationRepository`.
- Método de listagem por consulta no `EvolutionRepository`.
- Casos de uso de detalhe e atualização no `ConsultationService`.
- Caso de uso para listar evoluções vinculadas.
- Schema `ConsultationUpdateRequest`.
- Controllers e dependências necessárias.
- Auditoria da atualização.
- Documentação OpenAPI dos novos endpoints.

## Critérios de Aceite

- [ ] Consulta pode ser consultada individualmente.
- [ ] Consulta pode ser atualizada via `PUT`.
- [ ] Atualização preserva identidade, médico, paciente e data de criação.
- [ ] Atualização gera auditoria atômica sem expor conteúdo sensível em eventos.
- [ ] Detalhe e atualização respeitam isolamento entre médicos.
- [ ] Evoluções vinculadas podem ser listadas por consulta.
- [ ] A listagem vinculada não retorna evoluções independentes ou de outra consulta.
- [ ] A listagem vinculada aplica paginação e ordenação cronológica.
- [ ] Não existe endpoint de exclusão de consulta.
- [ ] O contrato OpenAPI representa os novos endpoints.
- [ ] `pytest -q` e `ruff check app alembic` passam sem erros.

## Testes Obrigatórios

- Testes unitários de detalhe e atualização do service.
- Testes de atualização com auditoria atômica.
- Testes de isolamento entre médicos.
- Testes de `404` para consulta inexistente ou inacessível.
- Testes de listagem paginada das evoluções vinculadas.
- Testes garantindo que evoluções independentes não aparecem na consulta.
- Testes do contrato OpenAPI para os três novos endpoints.

## Fora do Escopo

- Exclusão ou cancelamento de consulta.
- Agendamento de consulta.
- Assinatura ou finalização clínica.
- Geração automática de evolução ao criar ou atualizar consulta.
- Alteração do vínculo de uma evolução por endpoints de consulta.
- Filtros avançados de consultas.

## Definição de Concluído

A task estará concluída quando a API permitir consultar e atualizar uma consulta
e listar suas evoluções vinculadas, mantendo isolamento multi-tenant, auditoria
atômica e separação explícita entre os domínios de consulta e evolução.
