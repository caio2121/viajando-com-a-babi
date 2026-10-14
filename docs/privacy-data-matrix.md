# Matriz de dados, finalidade e retenção

Esta matriz é técnica e factual. Não define base legal nem substitui revisão
profissional. Qualquer item sem decisão da empresa permanece
`VALIDAÇÃO JURÍDICA NECESSÁRIA` e bloqueia publicação do conteúdo correspondente.

| Dado/identificador | Origem | Finalidade | Armazenamento/processador | Retenção proposta | Acesso | Exclusão/atendimento | Estado |
|---|---|---|---|---|---|---|---|
| Preferência de consentimento | navegador, chave `vcb_consent_analytics` | lembrar aceite/recusa | localStorage do navegador | até revogação/expiração definida | página e scripts de consentimento | limpar localStorage e atualizar estado | técnico parcial |
| GA4 Measurement ID e eventos | navegador após estado de consentimento | medir navegação/conversão | Google Analytics | política Google + decisão da empresa | operador autorizado/Google | revogar e solicitar procedimentos ao fornecedor | `VALIDAÇÃO JURÍDICA NECESSÁRIA` |
| Google Ads conversion ID/evento | navegador após consentimento | medir campanha/lead | Google Ads | política Google + decisão da empresa | operador autorizado/Google | revogar e procedimento do fornecedor | `VALIDAÇÃO JURÍDICA NECESSÁRIA` |
| Clique/URL WhatsApp | navegador | abrir contato comercial | WhatsApp e dispositivo; backend não persiste o texto observado | política comercial/WhatsApp | empresa e provedor do canal | procedimento do canal | `VALIDAÇÃO JURÍDICA NECESSÁRIA` |
| IP de tentativa administrativa | conexão HTTP | diagnóstico de falha de login | log do backend | definir retenção mínima operacional | operador técnico | rotação/redaction | pendente |
| Cookie de sessão admin | resposta de login | manter autenticação e CSRF | navegador + assinatura/segredo no processo | expiração atual; revogação futura | backend e navegador do operador | logout, expiração e rotação | técnico parcial |
| Senha administrativa | operador | autenticação | variável de ambiente; não persistir em tabela/log | até troca/rotação | processo, nunca frontend | remover secret e reiniciar | local-only |
| Usuário/role futuro | operador | autorização individual | SQLite futuro | enquanto conta ativa + retenção de auditoria | RBAC | desativar; exportar/excluir conforme decisão | planejado |
| Oferta, preço e destino | provider/admin | catálogo público | SQLite, snapshots e HTML gerado | último estado válido + prazo comercial | público/admin | arquivar e limpar conforme histórico | operacional |
| `external_id`/provider | integração | idempotência e rastreio | SQLite/sync history | enquanto reconciliação for necessária | backend/admin | retenção histórica definida por negócio | operacional |
| Imagem e metadata | asset/provider/admin | catálogo, acessibilidade e compartilhamento | repositório hoje; storage de mídia futuro | licença/retensão | público/admin | desvincular, quarentenar e remover | pendente |
| Logs estruturados futuros | runtime/jobs | observabilidade e incidente | stdout/collector futuro | rotação aprovada | operadores mínimos | purge/anonimização | planejado |
| Audit events | admin/jobs | integridade e prestação de contas | SQLite append-only com purge controlado | 365 dias por padrão (`AUDIT_RETENTION_DAYS`, faixa 30–3650) | endpoint restrito a admin | purge transacional autorizado; não há exclusão direta | técnico local; validação jurídica necessária |
| Backup banco/mídia futuro | job | disponibilidade/DR | destino externo cifrado | RPO/RTO/retention aprovados | operadores de recuperação | expiração sem remover único backup | planejado |

## Checklist técnico de consentimento

- [ ] Estado recusado não faz requisições de analytics/Ads não essenciais.
- [ ] Estado aceito carrega somente categorias aprovadas.
- [ ] Revogação impede novos eventos e deixa a preferência visível.
- [ ] Scripts de terceiros são inventariados por URL, finalidade e fornecedor.
- [ ] Eventos não carregam nome, telefone, mensagem ou outro conteúdo de
  formulário/WhatsApp.
- [ ] Captura de rede denied/granted/revoked é anexada à revisão.

## Checklist de retenção e direitos

- [ ] Owner empresarial definido para cada prazo.
- [ ] Logs, sessões, mídia órfã, histórico, auditoria e backups têm janela.
- [ ] Procedimento de acesso/exportação é definido antes de receber solicitação.
- [ ] Exclusão/anonymização não quebra integridade nem remove evidência necessária.
- [ ] Operadores/terceiros e solicitações ao fornecedor estão documentados.
- [ ] Decisões jurídicas estão registradas e não são inferidas pelo código.

## Evidência coletada

- `_partials/ga4.html` define Consent Mode com armazenamento negado por padrão e
  IDs de GA4/Ads.
- `_partials/cookie-banner.html` oferece aceite/recusa e persiste a escolha no
  navegador.
- `backend/app.py` usa cookie administrativo assinado e registra o endereço em
  falha de autenticação.
- `backend/app.py` grava `ip_hash`, não o IP, em `audit_events`; o endpoint
  administrativo expõe somente eventos para papel `admin` e aplica a janela
  configurada de retenção.
- `docs/analytics-pacotes.md` descreve eventos sem PII de formulários.

Esses fatos não provam conformidade. A implementação deve anexar captura de
rede e validação profissional antes do gate final.
