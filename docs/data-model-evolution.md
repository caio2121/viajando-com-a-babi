# Evolução do modelo de dados

## Status e limites

Este documento é o contrato de planejamento da evolução do SQLite local. A
`migrations/001_initial.sql` permanece imutável e nenhuma migration nova é
aplicada por esta task. A produção estática, o fallback HTML e o snapshot
`data/operator-sync.json` continuam inalterados.

O modelo abaixo separa o núcleo do catálogo das preocupações que ainda serão
implementadas: mídia, identidade administrativa, auditoria, overrides de
provider e jobs. A implementação deve ser incremental, compatível com os
registros atuais e sempre precedida de backup no ambiente que receber a
migration.

## Modelo atual

```text
offers
  id (PK)
  source, provider, external_id (UNIQUE)
  kind, title, catalog fields, status, ordering
  data_json, rendered_html
  created_at, updated_at

sync_runs
  id (PK)
  provider, source_reference, status, imported_count
  details_json, started_at, finished_at
```

Pontos de compatibilidade:

- `offers(provider, external_id)` continua sendo a identidade externa do
  registro automático;
- `data_json` continua disponível durante a transição para colunas/entidades
  normalizadas;
- `rendered_html` continua servindo o fallback e não deve ser recalculado por
  uma migration;
- pacotes manuais continuam distinguíveis por `source = 'manual'`;
- `sync_runs` continua sendo a referência de uma importação completa.

## ERD alvo incremental

```mermaid
erDiagram
    OFFERS ||--o{ OFFER_MEDIA : has
    MEDIA ||--o{ OFFER_MEDIA : attaches
    OFFERS ||--o{ OFFER_OVERRIDES : protects
    OFFERS ||--o{ OFFER_HISTORY : records
    PROVIDERS ||--o{ OFFERS : owns
    PROVIDERS ||--o{ SYNC_RUNS : executes
    SYNC_RUNS ||--o{ SYNC_RUN_ITEMS : contains
    OFFERS ||--o{ SYNC_RUN_ITEMS : reconciles
    USERS ||--o{ USER_ROLES : receives
    ROLES ||--o{ USER_ROLES : grants
    USERS ||--o{ AUDIT_EVENTS : performs
    JOBS ||--o{ JOB_RUNS : records
    USERS ||--o{ JOB_RUNS : triggers

    OFFERS {
      integer id PK
      text source
      text provider
      text external_id
      text kind
      text status
      text title
      text data_json_legacy
      text rendered_html_legacy
      integer version
      datetime deleted_at
      datetime created_at
      datetime updated_at
    }
    MEDIA {
      integer id PK
      text storage_key UK
      text media_type
      text mime_type
      integer byte_size
      integer width
      integer height
      text checksum
      text alt_text
      text rights_status
      text source_url
      datetime created_at
      datetime deleted_at
    }
    OFFER_MEDIA {
      integer offer_id FK
      integer media_id FK
      text role
      integer display_order
      datetime created_at
    }
    OFFER_OVERRIDES {
      integer id PK
      integer offer_id FK
      text field_name
      text value_json
      text reason
      integer created_by FK
      datetime created_at
      datetime deleted_at
    }
    OFFER_HISTORY {
      integer id PK
      integer offer_id FK
      integer sync_run_id FK
      text change_type
      text before_json
      text after_json
      datetime created_at
    }
    PROVIDERS {
      text code PK
      text display_name
      text adapter_version
      text status
      datetime created_at
      datetime updated_at
    }
    SYNC_RUNS {
      integer id PK
      text provider FK
      text source_reference
      text status
      text snapshot_checksum
      integer imported_count
      text details_json
      datetime started_at
      datetime finished_at
    }
    SYNC_RUN_ITEMS {
      integer id PK
      integer sync_run_id FK
      integer offer_id FK
      text external_id
      text status
      text error_code
      text details_json
    }
    USERS {
      integer id PK
      text username UK
      text password_hash
      text status
      datetime last_login_at
      datetime created_at
      datetime updated_at
    }
    ROLES {
      text code PK
    }
    USER_ROLES {
      integer user_id FK
      text role_code FK
    }
    AUDIT_EVENTS {
      integer id PK
      integer actor_user_id FK
      text action
      text resource_type
      text resource_id
      text request_id
      text ip_hash
      text change_json
      datetime created_at
    }
    JOBS {
      text code PK
      text status
      integer timeout_seconds
      integer retry_limit
      datetime created_at
    }
    JOB_RUNS {
      integer id PK
      text job_code FK
      integer triggered_by FK
      text lock_key
      text status
      text error_code
      text details_json
      datetime started_at
      datetime finished_at
    }
```

O diagrama é um alvo de domínio, não uma instrução para criar todas as
tabelas em uma única migration. Colunas `password_hash`, `change_json` e
`details_json` têm regras próprias de acesso, retenção e redaction definidas
nas tasks de segurança, dados e privacidade.

## Invariantes e constraints

1. `offers(provider, external_id)` permanece único para registros externos.
2. `source`, `kind`, `status`, `media.role`, `rights_status` e estados de job
   usam `CHECK`/allowlist; valores desconhecidos são rejeitados.
3. Relações entre oferta, mídia, override, histórico, usuário e job usam
   foreign keys com `PRAGMA foreign_keys = ON` em toda conexão.
4. `offer_media(offer_id, media_id, role)`, `user_roles(user_id, role_code)` e
   `sync_run_items(sync_run_id, external_id)` são únicos para impedir vínculos
   duplicados e reprocessamento ambíguo.
5. Exclusões de catálogo e mídia são soft delete/quarentena quando houver
   dependência histórica ou de backup; limpeza física é uma operação separada.
6. Alterações de uma oferta e seus eventos de auditoria acontecem na mesma
   transação.
7. Sync automático é idempotente por `(provider, external_id)` e não pode
   apagar o last-known-good por falha parcial.
8. Overrides manuais não são armazenados como uma mutação indistinguível do
   valor recebido pelo provider.
9. Timestamps são UTC em formato consistente e `updated_at` muda em toda
   alteração de negócio.
10. Índices são adicionados somente após `EXPLAIN QUERY PLAN` e workload
   representativo; não se indexa toda coluna por padrão.

## Plano de migrations

| Versão proposta | Conteúdo | Compatibilidade e rollback |
|---|---|---|
| `001_initial.sql` | Schema atual de `offers` e `sync_runs` | Já aplicada; nunca editar. |
| `002_offer_lifecycle.sql` | `version`, `deleted_at`, referência segura de sync e constraints compatíveis | Backfill idempotente; restore do backup pré-migration. |
| `003_media.sql` | `media` e `offer_media`, incluindo índices e estados | Não altera `image_url` existente; dual-read até validação. |
| `004_provider_sync.sql` | `providers`, `sync_run_items`, checksum e reconciliação | Importa em staging e só promove lote validado. |
| `005_admin_identity.sql` | `users`, `roles`, `user_roles`, sessões/revogação conforme desenho de segurança | Migração inicia sem remover o acesso local legado; remoção só após testes. |
| `006_audit.sql` | `audit_events` e índices de consulta restrita | Eventos novos são append-only; retenção documentada. |
| `007_overrides_history.sql` | `offer_overrides` e `offer_history` | Reprocessamento do snapshot deve ser determinístico. |
| `008_jobs.sql` | `jobs`, `job_runs` e locks/leases | Jobs começam desabilitados até observabilidade e testes. |

As versões são uma sequência proposta. A ordem definitiva, SQL e backfill só
serão criados nas tasks filhas correspondentes, após revisão do ERD e testes em
banco limpo e fixture existente.

## Política de execução e rollback

1. Gerar backup verificável de banco e mídia antes de qualquer migration.
2. Executar migration em cópia limpa e em fixture representativa do banco
   atual; comparar contagens, constraints e `PRAGMA integrity_check`.
3. Marcar a versão em `schema_migrations` somente após o script inteiro
   concluir; falha deve fazer rollback da transação quando suportado.
4. Não editar migration aplicada. Correção posterior recebe nova versão ou
   restaura o backup pré-migration e aplica um forward-fix revisado.
5. Readiness, smoke público/admin e integridade das referências de mídia são
   pré-requisitos para promover o artefato.
6. Nenhuma migration deste plano deve ser executada contra produção nesta
   etapa do projeto.

## Decisões pendentes

- confirmar se `provider` continuará texto controlado ou será FK para
  `providers` após o primeiro backfill;
- definir retenção de `offer_history`, `audit_events`, backups e mídia órfã;
- definir política de criptografia em repouso e destino externo dos backups;
- validar juridicamente campos que possam conter dados pessoais;
- escolher estratégia futura de object storage sem acoplar o domínio ao
  fornecedor.

## Auditoria implementada nesta etapa

`migrations/005_audit_append_only.sql` torna `audit_events` append-only, com
exceção técnica de purge controlado pela janela `AUDIT_RETENTION_DAYS` (365
dias por padrão, configurável entre 30 e 3650). A leitura ocorre somente em
`/api/admin/audit` para o papel `admin`; segredos não são armazenados e a
origem é representada por hash. A definição jurídica do prazo e do owner
empresarial continua necessária antes de produção.

Essas decisões não podem ser inferidas apenas do schema atual e devem ser
registradas antes das migrations correspondentes.
