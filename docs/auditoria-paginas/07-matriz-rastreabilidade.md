# Matriz de rastreabilidade

| ID | Requisito/critério | Implementação ou evidência | Verificação | Estado |
|---|---|---|---|---|
| R01 | Seis páginas legais sem aparência de placeholder | `_build_legal_pages.py` e seis HTML legais | `test_legal_pages_are_complete_and_indexable` | Atendido |
| R02 | Não inventar taxas, prazos ou obrigações | redação condicional e pendências em `03` e `08` | inspeção de conteúdo + revisão independente | Atendido com validação jurídica pendente |
| R03 | Layout compartilhado | partials de header, footer, head e GA4 | geração e leitura dos HTML | Atendido |
| R04 | Consentimento antes das tags | `_partials/ga4.html` e banner | fluxo browser aceitar/recusar | Atendido |
| R05 | Revogar consentimento | `VCBConsent.revoke()` e `cookies.html#revokeConsent` | fluxo browser de revogação | Atendido |
| R06 | Formulário exige campos essenciais | `required`, `min=1`, ausência de `novalidate` | unittest + `checkValidity` no browser | Atendido |
| R07 | Links internos resolvem | links relativos dos HTML do root | `test_internal_links_resolve_to_repository_files` | Atendido |
| R08 | Canonical e sitemap legais | gerador e `sitemap.xml` | unittest de metadata e sitemap | Atendido |
| R09 | Navegação acessível básica | skip link, foco, labels, status live | inspeção + browser direcionado | Atendido parcialmente; sem certificação WCAG |
| R10 | Documentação da auditoria | `docs/auditoria-paginas/00` a `09` | listagem/leitura dos arquivos | Atendido após criação |
| R11 | Revisão independente | subagente `review` | parecer anexado à task 1478 e `09` | Pendente até o ciclo de revisão |

## Critérios fora do escopo de código

A definição de retenção, contrato de fornecedores, taxas de cancelamento, designação formal de encarregado, registros comerciais e aprovação jurídica dependem de decisão e evidência da empresa. Não são considerados atendidos por texto genérico no site.
