# Task: Endurecimento do Fluxo de Auditoria

## Objetivo

Garantir que toda escrita auditada seja persistida de forma atômica com seu
registro de auditoria e evento de domínio, sem expor estados sensíveis em texto
claro no `domain_event`.

Esta é uma task transversal e deve ser concluída antes da implementação de
novas entidades clínicas, incluindo `Evolution`.

## Problemas Atuais

- Os repositórios executam `commit` antes da criação do registro de auditoria.
- Uma falha posterior na auditoria ou publicação do evento pode deixar a
  alteração persistida sem rastreabilidade.
- O `domain_event.payload` replica `before_state` e `after_state`, incluindo
  dados clínicos e pessoais em texto claro.
- O controle da transação está dividido entre repositories,
  `AuditEventService` e `DomainEventBus`.

## Escopo

### Transação Atômica

- Tornar a escrita da entidade, do `audit_log` e do `domain_event` uma única
  transação de banco.
- Remover `commit` dos métodos de escrita dos repositórios auditados.
- Usar `flush` e `refresh` nos repositórios quando necessário para retornar o
  estado persistido sem concluir a transação.
- Centralizar o `commit` no fluxo de auditoria, somente após entidade,
  auditoria e evento terem sido adicionados com sucesso à mesma sessão.
- Executar `rollback` e propagar o erro quando qualquer etapa da operação
  falhar.

### Sanitização dos Eventos de Domínio

- Remover `before_state` e `after_state` do `domain_event.payload`.
- Manter no evento apenas metadados necessários ao processamento:
  - `entity_type`
  - `entity_id`
  - `action`
  - `doctor_id`
  - `request_id`
- Preservar os estados completos exclusivamente no `audit_log`, utilizando a
  criptografia já aplicada em `before_state` e `after_state`.

### Entidades Afetadas

Aplicar o novo fluxo a todas as escritas auditadas existentes:

- `Doctor`
- `Patient`
- `Consultation`
- `Disease`
- `Medication`
- `Image`
- `Lesion`

## Direção de Implementação

- Repositories continuam responsáveis somente pela persistência e consulta de
  suas entidades, sem decidir quando a transação deve ser concluída.
- Services continuam responsáveis por executar o caso de uso e informar os
  estados anterior e posterior ao `AuditEventService`.
- `AuditEventService.record_write` deve registrar auditoria, publicar o evento
  sanitizado e concluir a transação.
- O mesmo `AsyncSession` deve ser compartilhado pelo repository,
  `AuditEventService` e `DomainEventBus`.
- Escritas de negócio não devem ser concluídas sem o serviço de auditoria.
- O processamento posterior de eventos pendentes continua responsável por sua
  própria transação.

## Critérios de Aceite

- [ ] Nenhuma escrita auditada é persistida se o registro de auditoria falhar.
- [ ] Nenhuma escrita auditada é persistida se a publicação do evento falhar.
- [ ] Escrita da entidade, `audit_log` e `domain_event` é concluída por um único
      `commit`.
- [ ] Falhas executam `rollback` antes de serem propagadas.
- [ ] Repositórios auditados não executam `commit`.
- [ ] `domain_event.payload` não contém `before_state`, `after_state` nem
      conteúdo clínico em texto claro.
- [ ] `audit_log.before_state` e `audit_log.after_state` continuam armazenando
      os estados necessários à rastreabilidade.
- [ ] Todas as escritas existentes continuam gerando auditoria e evento.
- [ ] Testes existentes continuam verdes.
- [ ] `ruff check app alembic` passa sem erros.

## Testes Obrigatórios

- Testar que uma falha ao gravar o `audit_log` impede a persistência da
  entidade.
- Testar que uma falha ao publicar o evento impede a persistência da entidade e
  da auditoria.
- Testar que uma operação bem-sucedida gera entidade, auditoria e evento na
  mesma transação.
- Testar que o evento contém somente os metadados permitidos.
- Testar que estados sensíveis permanecem disponíveis no `audit_log`.
- Cobrir ao menos uma criação, uma atualização e uma exclusão auditada.
- Executar a suíte completa para detectar regressões nas entidades existentes.

## Fora do Escopo

- Alterações funcionais nas entidades existentes.
- Novos endpoints públicos de auditoria.
- Consulta pública ao histórico de alterações.
- Assinatura digital ou certificação de documentos.
- Alterações na UI ou no cliente Dart.

## Dependências e Impactos

- Esta task bloqueia `task_evolutions_backend.md`.
- A mudança afeta todos os services e repositories que realizam escritas
  auditadas.
- Deve ser validado que fluxos especiais, como confirmação de upload de
  imagens, continuam concluindo suas transações corretamente.

## Definição de Concluído

A task estará concluída quando todas as escritas auditadas existentes forem
atômicas, os eventos de domínio não carregarem estados sensíveis e os critérios
de aceite estiverem cobertos por testes automatizados.
