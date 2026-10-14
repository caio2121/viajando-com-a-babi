# Índice operacional da documentação

Este índice é a entrada para desenvolvimento, administração, operação e
release. Cada documento deve informar escopo, pré-requisitos, evidência e
limites. Segredos e dados pessoais nunca são colocados aqui.

## Começar

| Público | Documento | Estado |
|---|---|---|
| Todos | [README do projeto](../README.md) | existente |
| Dev/ops | [Arquitetura dinâmica local](dynamic-local-architecture.md) | local-only |
| Dev/ops | [Evolução do modelo de dados](data-model-evolution.md) | plano |
| Dev/ops | [Estratégia de testes](test-strategy.md) | baseline + plano |

## Segurança e dados

| Documento | Owner sugerido | Evidência/pendência |
|---|---|---|
| [Modelo de ameaças](security-threat-model.md) | segurança | threat scenarios e DAST |
| [Classificação de dados](data-classification.md) | produto + segurança | retenção e acesso |
| [Matriz de privacidade](privacy-data-matrix.md) | produto + jurídico | consentimento e direitos |
| [Requisitos legais](legal-requirements.md) | empresa + jurídico | dados oficiais e aprovação |
| [Baseline de supply chain](supply-chain-inventory.md) | engenharia | SBOM, scans e SHA/digest |

## Qualidade do produto

| Documento | Owner sugerido | Evidência/pendência |
|---|---|---|
| [Baseline SEO](seo-crawl-baseline.md) | SEO | crawler HTTP, schema e redirects |
| [Baseline de performance](performance-baseline.md) | engenharia | mobile, API load e budgets aprovados |
| [Analytics de pacotes](analytics-pacotes.md) | marketing | consentimento e DebugView |
| [Funil offline](funil-offline.md) | negócio | operação comercial |
| [SEO histórico](seo-baseline.md) | SEO | Search Console e PSI |

## Operação futura

As páginas abaixo devem ser criadas/validadas pelas tasks correspondentes antes
da promoção:

- desenvolvimento, admin, migrations e integração;
- mídia, storage e limpeza de órfãos;
- observabilidade, incidentes e troubleshooting;
- backup, restore e Disaster Recovery Drill;
- staging, deploy, migration preflight e rollback;
- segurança, supply chain e release notes;
- Production Readiness Review.

## Regra de manutenção

1. Documento novo entra neste índice com público, owner e estado.
2. Comando operacional deve ter check de resultado e indicar se é read-only,
   mutável ou destrutivo de laboratório.
3. Conteúdo jurídico/empresarial sem fonte oficial recebe
   `VALIDAÇÃO JURÍDICA NECESSÁRIA`.
4. Link quebrado, evidência expirada ou procedimento não testado reabre a task
   correspondente.
5. O índice não substitui os artifacts das tasks nem o gate final.
