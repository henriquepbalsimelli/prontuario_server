# RBAC do Grafana

## Modelo adotado (Grafana OSS)
- `Viewer`: apenas leitura de dashboards e Explore.
- `Editor`: criação/edição de dashboards e queries.
- `Admin`: gestão de usuários, datasources e configurações da organização.

## Política mínima
- Não usar usuário admin no dia a dia.
- Criar contas nominativas por pessoa.
- Permitir perfil `Admin` somente para time de plataforma.
- Times de produto/engenharia devem usar `Editor` ou `Viewer` conforme necessidade.

## Processo de onboarding
1. Criar usuário no Grafana.
2. Atribuir papel organizacional (`Viewer`/`Editor`/`Admin`).
3. Validar acesso apenas às pastas/dashboards necessários.

## Processo de revisão
- Revisão de acessos a cada 30 dias.
- Revogar acesso imediatamente em desligamento ou mudança de função.

## Hardening adicional
- `GF_USERS_ALLOW_SIGN_UP=false`
- `GF_AUTH_ANONYMOUS_ENABLED=false`
- senha de admin forte e rotacionada
