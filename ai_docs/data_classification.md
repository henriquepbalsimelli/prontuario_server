# Classificação de Dados Sensíveis

## Objetivo
Formalizar a classificação de dados do Prontuário Dermatológico para orientar:
- criptografia em trânsito e em repouso;
- criptografia de campo (application-level);
- mascaramento de logs;
- controles de acesso e auditoria.

## Níveis de Classificação

### 1) PUBLIC
Dados sem sensibilidade clínica ou de identificação pessoal.

Controles mínimos:
- integridade de dados;
- acesso por perfil funcional.

### 2) INTERNAL
Dados internos operacionais sem conteúdo clínico direto.

Controles mínimos:
- acesso autenticado;
- retenção controlada;
- não expor em logs públicos.

### 3) SENSITIVE
Dados pessoais e clínicos que exigem proteção reforçada.

Controles obrigatórios:
- TLS em trânsito;
- criptografia em repouso;
- mascaramento em logs;
- princípio do menor privilégio.

### 4) HIGHLY_SENSITIVE
Dados críticos (credenciais, segredo criptográfico, dados clínicos de maior impacto).

Controles obrigatórios:
- TLS em trânsito;
- criptografia em repouso;
- criptografia de campo (quando armazenado em banco/app);
- acesso estritamente restrito e auditado;
- rotação de chaves e versionamento.

## Regras Gerais
1. `doctor_id` e isolamento multi-tenant são obrigatórios em todo acesso clínico.
2. Campos `SENSITIVE` e `HIGHLY_SENSITIVE` não podem ser logados em claro.
3. Campos `HIGHLY_SENSITIVE` devem usar criptografia de campo quando persistidos fora de cofre de segredos.
4. Segredos operacionais (ex.: `JWT_SECRET_KEY`, credenciais de banco) devem vir de secret manager.

## Mapeamento Inicial por Entidade

### Doctor
- `id`: INTERNAL
- `name`: SENSITIVE
- `email`: SENSITIVE
- `password_hash`: HIGHLY_SENSITIVE
- `created_at`: INTERNAL

### Patient
- `id`: INTERNAL
- `doctor_id`: INTERNAL
- `name`: SENSITIVE
- `birth_date`: SENSITIVE
- `gender`: SENSITIVE
- `phone`: SENSITIVE
- `notes`: HIGHLY_SENSITIVE
- `created_at`: INTERNAL

### Consultation
- `id`: INTERNAL
- `doctor_id`: INTERNAL
- `patient_id`: INTERNAL
- `consultation_date`: SENSITIVE
- `chief_complaint`: HIGHLY_SENSITIVE
- `physical_exam`: HIGHLY_SENSITIVE
- `conduct`: HIGHLY_SENSITIVE
- `created_at`: INTERNAL

### Disease / Medication
- catálogos públicos técnicos: PUBLIC/INTERNAL

### Image
- `s3_key`: HIGHLY_SENSITIVE
- metadados clínicos (`type`, `body_region`, `coord_x`, `coord_y`): SENSITIVE
- vínculos (`doctor_id`, `patient_id`, `consultation_id`): INTERNAL

### Lesion
- `label`, `body_region`, `status`: SENSITIVE
- `notes`: HIGHLY_SENSITIVE
- coordenadas corporais: SENSITIVE

### Evolution
- `doctor_id`, `patient_id`, `consultation_id`, `created_at`, `updated_at`: INTERNAL
- `origin_type`, `occurred_at`: SENSITIVE
- `content`: HIGHLY_SENSITIVE

### AuditLog
- `doctor_id`, `entity_type`, `entity_id`, `action`, `created_at`: INTERNAL
- `before_state`, `after_state`: HIGHLY_SENSITIVE
- `ip_address`, `user_agent`: SENSITIVE

### DomainEvent
- `event_type`, `entity_id`, `created_at`, `processed`: INTERNAL
- `payload`: SENSITIVE ou HIGHLY_SENSITIVE (dependendo do conteúdo)

## Diretrizes de Implementação (próximas etapas)
1. Adicionar utilitário de classificação central no código.
2. Integrar classificação com masking de logs.
3. Integrar classificação com política de criptografia por campo.
4. Cobrir classificação e masking com testes unitários.
