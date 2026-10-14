# Classificação de dados e fronteiras

## Escopo e premissas verificadas

Este inventário descreve o estado local observado e não é parecer jurídico. A
aplicação dinâmica usa SQLite em volume Docker; o banco não é publicado por uma
porta própria no `compose.yaml`. A produção atual continua sendo o site estático
no GitHub Pages.

Quando a finalidade, base legal, prazo ou operador depender de decisão da
empresa, o registro permanece `VALIDAÇÃO JURÍDICA NECESSÁRIA`.

## Matriz dado → origem → finalidade → armazenamento → retenção → acesso → exclusão

| Dado/ativo | Origem | Finalidade observada | Armazenamento atual | Retenção | Acesso | Exclusão |
|---|---|---|---|---|---|---|
| Oferta e preço públicos | snapshot/provider e admin manual | exibir catálogo e CTA | SQLite `offers`, JSON/HTML estático e cache de build | último estado válido; prazo comercial pendente | público; admin conforme origem | arquivar/gerenciar no catálogo; prazo comercial pendente |
| Identificador externo da oferta | provider | upsert idempotente | SQLite `offers.external_id`, snapshot | enquanto histórico de integração for necessário | backend/admin | junto da oferta; retenção histórica pendente |
| Fragmento HTML renderizado | pipeline/provider | fallback e paridade visual | SQLite `rendered_html`, `data/generated`, páginas | enquanto fallback/release existir | público/admin indireto | remover em rebuild/limpeza aprovada |
| Imagem e URL de origem | assets/provider/admin | capa e compartilhamento | repositório/assets hoje; futuro storage de mídia | licença/retensão pendente | público; admin operacional | remover vínculo, quarentena e limpeza aprovada |
| Senha administrativa | operador/env | autenticar admin local | variável de ambiente; não deve ir para banco/log | enquanto configurada; rotação pendente | processo de backend | remover `.env`/secret e reiniciar |
| Segredo de sessão | backend/env + cookie | autenticar sessão e CSRF | env no processo; cookie HttpOnly no navegador | expiração atual da sessão; política de revogação pendente | backend/navegador do operador | logout/expiração/rotação |
| IP/endereço do cliente | conexão HTTP/log de falha | diagnóstico de autenticação | log do backend (`address_string`) | retenção de log pendente | operador autorizado | rotação/redaction conforme política |
| Eventos de analytics/Ads | navegador e terceiros | métricas de conversão, conforme consentimento | localStorage de consentimento e serviços Google | política de terceiro; `VALIDAÇÃO JURÍDICA NECESSÁRIA` | fornecedor/operador autorizado | revogar consentimento; solicitação ao fornecedor |
| Mensagem/contato WhatsApp | navegador → WhatsApp | atendimento comercial | não é persistida pelo backend local observado | política da empresa/WhatsApp; `VALIDAÇÃO JURÍDICA NECESSÁRIA` | empresa e WhatsApp conforme canal | procedimento no canal/empresa |
| Logs técnicos | backend/container | diagnóstico e disponibilidade | stdout/log driver futuro | definir rotação/retention | operadores mínimos | rotação segura e purge |
| Backup banco + mídia | job futuro | disponibilidade/DR | destino externo criptografado futuro | política RPO/RTO/retention futura | operadores de recuperação | expiração controlada; não apagar único backup válido |
| Dados jurídicos/empresariais | fornecimento futuro da empresa | identificação e transparência | configuração/páginas legais futuras | conforme validação profissional | público/admin | alterar versão aprovada |

## Classificação CIA

| Grupo | Confidencialidade | Integridade | Disponibilidade | Controle mínimo |
|---|---|---|---|---|
| Catálogo público | baixa | alta | alta | validação server-side, transação e last-known-good |
| Credenciais/sessão | alta | alta | média | secret injection, hash/rotação, cookie seguro, redaction |
| Logs/auditoria | média | alta | média | acesso mínimo, redaction, rotação e append-only para auditoria |
| Banco/mídia | média/alta | alta | alta | volume não público, FK, backup, checksum e restore |
| Backups | alta | alta | alta | criptografia, cópia externa, retenção e DR drill |
| Analytics/terceiros | conforme identificador | média | baixa | consentimento efetivo, minimização e revisão de fornecedor |

## Fronteiras de confiança

```text
navegador público
  └─> HTML/API pública ──> processo backend ──> SQLite + volume de mídia

navegador admin
  └─> login/sessão/CSRF ──> endpoints administrativos ──> banco/mídia/auditoria

provider externo ──> adapter/validação ──> staging de sync ──> publicação atômica

CI/repositório ──> imagem imutável ──> runtime
runtime ──> backup criptografado externo
```

O banco e a mídia não devem ter porta pública própria. O acesso de operação deve
ser pelo processo autorizado, scripts de backup/restore e volumes protegidos.

## Controles obrigatórios derivados

1. Não registrar senha, token, cookie, payload sensível ou mensagem completa em
   logs.
2. Não enviar PII para analytics/Ads sem decisão, minimização e consentimento
   efetivo quando aplicável.
3. Separar dados públicos de credenciais, sessão, logs e backups.
4. Definir owner, prazo e evidência para cada retenção antes do release.
5. Nenhum banco remoto, secret real ou backup externo será configurado nesta
   etapa local.
6. Qualquer pedido de titular, base legal, operador ou retenção jurídica exige
   `VALIDAÇÃO JURÍDICA NECESSÁRIA` antes de publicação.

## Pendências bloqueadoras

- Aprovar retenção e descarte de logs, histórico, mídia órfã e backups.
- Confirmar se algum formulário futuro persistirá dados pessoais no backend.
- Confirmar operadores de analytics, Ads, WhatsApp e operadoras.
- Definir criptografia em repouso e destino externo dos backups.
- Confirmar owner empresarial e jurídico para itens marcados acima.
