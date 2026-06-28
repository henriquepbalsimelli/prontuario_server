**Agenda Médica V0**

**Summary**
- Evoluir `consultation` para também representar agendamento.
- Paciente será obrigatório no agendamento.
- A agenda exibirá períodos variáveis de `1, 3, 5, 7, 14` dias, com calendário mensal/anual calculado no Flutter.
- Backend retornará consultas por intervalo de data/hora do médico.

**Key Changes**
- Backend:
  - Adicionar em `consultation`: `scheduled_start_at`, `scheduled_end_at`, `status`.
  - Status V0: `scheduled`, `completed`, `cancelled`.
  - Manter `consultation_date` por compatibilidade, preenchendo/derivando a data quando houver `scheduled_start_at`.
  - Criar endpoint médico-escopado: `GET /consultations?start_at=&end_at=&status=`.
  - Estender `POST /patients/{patient_id}/consultations` e `PUT /consultations/{id}` para aceitar horário e status.
  - Validar que `scheduled_end_at > scheduled_start_at` e bloquear sobreposição para o mesmo médico quando status não for `cancelled`.
  - Migração Alembic com índice por `(doctor_id, scheduled_start_at)`.

- Frontend:
  - Substituir placeholder da agenda por `AgendaSection` integrada ao módulo existente.
  - Criar `AgendaController` e `AgendaApi` usando `Dio`.
  - Criar helper puro de calendário para gerar dias, semanas, meses e ano no cliente, sem endpoint extra.
  - Grade padrão: 08:00-18:00, slots de 30 minutos, com cards de consultas posicionados por horário.
  - Controle de densidade: `1, 3, 5, 7, 14 dias`.
  - Formulário/modal de agendamento com paciente obrigatório, busca de paciente existente, data, hora inicial, duração padrão 30 min, status e campos clínicos opcionais.
  - Ao clicar em consulta marcada, abrir detalhe com ações: editar, cancelar, marcar realizada, abrir prontuário/consulta.

**Public Interfaces**
- `ConsultationCreateRequest` / `ConsultationUpdateRequest`:
  - `scheduled_start_at: datetime | null`
  - `scheduled_end_at: datetime | null`
  - `status: "scheduled" | "completed" | "cancelled" | null`
- `ConsultationResponse` incluirá os mesmos campos.
- Novo método de repositório/serviço: listar consultas por intervalo do médico.
- Regra de tempo: armazenar datetimes timezone-aware; UI exibe em horário local.

**Test Plan**
- Backend: testes de schema OpenAPI, criação com horário, listagem por intervalo, bloqueio de sobreposição, cancelamento liberando conflito, e compatibilidade de consultas antigas sem horário.
- Frontend: testes do helper de calendário, controller de agenda, estados vazio/loading/erro, troca de densidade, criação de agendamento e clique para abrir consulta.
- Rodar `pytest` em `prontuario_api` e `flutter test` em `prontuario_ui`.

**Assumptions**
- V0 não terá secretária nem permissões novas; o desenho mantém tudo por `doctor_id` para permitir um ator “secretária” depois.
- Agendamentos sem paciente ficam fora do escopo inicial.
- Feriados, horários personalizados por médico, recorrência, confirmação automática e lista de espera ficam para fases futuras.
